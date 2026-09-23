import math
import re
from datetime import datetime, timezone
from sqlalchemy import text
from app.databases.config import engine
from app.databases.seeders.anchor_seeder import ensure_anchor, rebuild_anchors

TIMEFRAMES = ("m1", "m5", "m15", "m30", "h1", "h4", "d1", "w1", "mn1")
SYMBOL_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")
MAX_SYMBOL_LENGTH = 32

_ENSURED_TABLES = set()

CREATE_OHLC_TABLE = """
    CREATE TABLE IF NOT EXISTS `{table}` (
        id INT AUTO_INCREMENT PRIMARY KEY,
        symbol VARCHAR(50),
        open DECIMAL(15, 6),
        high DECIMAL(15, 6),
        low DECIMAL(15, 6),
        close DECIMAL(15, 6),
        time BIGINT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_{table} (symbol, time)
    )
"""

CREATE_SYMBOLS_TABLE = """
    CREATE TABLE IF NOT EXISTS symbols (
        id INT AUTO_INCREMENT PRIMARY KEY,
        server VARCHAR(100) NOT NULL DEFAULT '',
        name VARCHAR(100) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE KEY unique_symbol_server (server, name),
        INDEX idx_name (name)
    )
"""

CREATE_SYMBOL_RANGES_TABLE = """
    CREATE TABLE IF NOT EXISTS symbol_ranges (
        id INT AUTO_INCREMENT PRIMARY KEY,
        server VARCHAR(100) NOT NULL DEFAULT '',
        symbol VARCHAR(100) NOT NULL,
        timeframe VARCHAR(10) NOT NULL,
        first_ts DATETIME,
        last_ts DATETIME,
        count INT NOT NULL DEFAULT 0,
        UNIQUE KEY unique_symbol_range (server, symbol, timeframe)
    )
"""

CREATE_PAGE_ANCHOR_TABLE = """
    CREATE TABLE IF NOT EXISTS ohlc_page_anchor (
        symbol VARCHAR(32) NOT NULL,
        timeframe VARCHAR(10) NOT NULL,
        k INT NOT NULL,
        start_time INT NOT NULL,
        PRIMARY KEY (symbol, timeframe, k)
    )
"""


def ensure_tables(conn, table):
    if table in _ENSURED_TABLES:
        return False
    exists = bool(conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema = DATABASE() AND table_name = :table"
    ), {"table": table}).scalar())
    conn.execute(text(CREATE_OHLC_TABLE.format(table=table)))
    conn.execute(text(CREATE_SYMBOLS_TABLE))
    conn.execute(text(CREATE_SYMBOL_RANGES_TABLE))
    conn.execute(text(CREATE_PAGE_ANCHOR_TABLE))
    _ENSURED_TABLES.add(table)
    return not exists


def prepare(candle):
    symbol = candle.symbol.strip()
    if not symbol or len(symbol) > MAX_SYMBOL_LENGTH or not SYMBOL_PATTERN.match(symbol):
        raise ValueError(f"invalid symbol: {candle.symbol}")
    timeframe = candle.timeframe.strip().lower()
    if timeframe not in TIMEFRAMES:
        raise ValueError(f"invalid timeframe: {candle.timeframe}")
    if not all(math.isfinite(price) for price in (candle.open, candle.high, candle.low, candle.close)):
        raise ValueError("invalid price value")
    if candle.high < candle.low:
        raise ValueError("high must be greater than or equal to low")
    if candle.time <= 0:
        raise ValueError("invalid time")
    return {
        "server": candle.server.strip(),
        "symbol": symbol,
        "timeframe": timeframe,
        "table": f"ohlc_{symbol.lower()}_{timeframe}",
        "open": candle.open,
        "high": candle.high,
        "low": candle.low,
        "close": candle.close,
        "time": int(candle.time),
    }


def get_range_state(conn, item):
    row = conn.execute(text(
        "SELECT id, count, last_ts FROM symbol_ranges "
        "WHERE server = :server AND symbol = :symbol AND timeframe = :timeframe LIMIT 1"
    ), {"server": item["server"], "symbol": item["symbol"], "timeframe": item["timeframe"].upper()}).fetchone()
    if row:
        return row[0], int(row[1] or 0), int(row[2].timestamp()) if row[2] else None
    stats = conn.execute(text(
        f"SELECT COUNT(*), MAX(time) FROM `{item['table']}` WHERE symbol = :symbol"
    ), {"symbol": item["symbol"]}).fetchone()
    return None, int(stats[0] or 0), int(stats[1]) if stats[1] is not None else None


def candle_exists(conn, item):
    row = conn.execute(text(
        f"SELECT 1 FROM `{item['table']}` WHERE symbol = :symbol AND time = :time LIMIT 1"
    ), {"symbol": item["symbol"], "time": item["time"]}).fetchone()
    return row is not None


def save_candle(conn, item):
    conn.execute(text(
        f"INSERT INTO `{item['table']}` (symbol, open, high, low, close, time) "
        "VALUES (:symbol, :open, :high, :low, :close, :time) "
        "ON DUPLICATE KEY UPDATE open = VALUES(open), high = VALUES(high), "
        "low = VALUES(low), close = VALUES(close)"
    ), item)


def save_range(conn, item, range_id, count, inserted):
    stamp = datetime.fromtimestamp(item["time"], tz=timezone.utc).replace(tzinfo=None)
    delta = 1 if inserted else 0
    if range_id is not None:
        conn.execute(text(
            "UPDATE symbol_ranges SET first_ts = LEAST(first_ts, :stamp), "
            "last_ts = GREATEST(last_ts, :stamp), count = count + :delta WHERE id = :id"
        ), {"stamp": stamp, "delta": delta, "id": range_id})
        return
    conn.execute(text(
        f"INSERT INTO symbol_ranges (server, symbol, timeframe, first_ts, last_ts, count) "
        f"VALUES (:server, :symbol, :timeframe, :stamp, :stamp, :count) "
        f"ON DUPLICATE KEY UPDATE first_ts = LEAST(first_ts, VALUES(first_ts)), "
        f"last_ts = GREATEST(last_ts, VALUES(last_ts)), "
        f"count = (SELECT COUNT(*) FROM `{item['table']}` WHERE symbol = :symbol)"
    ), {"server": item["server"], "symbol": item["symbol"], "timeframe": item["timeframe"].upper(),
        "stamp": stamp, "count": count + delta})


def save_symbol(conn, item):
    conn.execute(text(
        "INSERT INTO symbols (server, name) VALUES (:server, :name) "
        "ON DUPLICATE KEY UPDATE server = server"
    ), {"server": item["server"], "name": item["symbol"]})


def upsert_candle(conn, item):
    range_id, count, last_time = get_range_state(conn, item)
    existed = candle_exists(conn, item)
    save_candle(conn, item)
    inserted = not existed
    anchors_rebuilt = False
    if inserted:
        if last_time is None or item["time"] > last_time:
            ensure_anchor(item["symbol"], item["timeframe"], conn, count, item["time"])
        else:
            rebuild_anchors(item["symbol"], item["timeframe"], conn)
            anchors_rebuilt = True
    save_range(conn, item, range_id, count, inserted)
    save_symbol(conn, item)
    return {
        "action": "created" if inserted else "updated",
        "symbol": item["symbol"],
        "timeframe": item["timeframe"],
        "table_created": item["table_created"],
        "anchors_rebuilt": anchors_rebuilt,
    }


def min_start_timestamp(value):
    if not value:
        return None
    try:
        moment = datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return int(moment.timestamp())


def skipped_result(item):
    return {
        "action": "skipped",
        "symbol": item["symbol"],
        "timeframe": item["timeframe"],
        "table_created": item["table_created"],
        "anchors_rebuilt": False,
    }


def preview_candles(candles, min_start_date=""):
    items = [prepare(candle) for candle in candles]
    min_start = min_start_timestamp(min_start_date)
    results = []
    for item in items:
        item["table_created"] = False
        if min_start is not None and item["time"] < min_start:
            results.append(skipped_result(item))
            continue
        results.append({
            "action": "dry_run",
            "symbol": item["symbol"],
            "timeframe": item["timeframe"],
            "table_created": False,
            "anchors_rebuilt": False,
        })
    return results


def ingest_candles(candles, min_start_date=""):
    items = [prepare(candle) for candle in candles]
    min_start = min_start_timestamp(min_start_date)
    with engine.begin() as conn:
        for item in items:
            item["table_created"] = ensure_tables(conn, item["table"])
    results = []
    pending_error = None
    for item in items:
        if min_start is not None and item["time"] < min_start:
            results.append(skipped_result(item))
            continue
        try:
            with engine.begin() as conn:
                results.append(upsert_candle(conn, item))
        except Exception as error:
            if pending_error is None:
                pending_error = error
    if pending_error is not None:
        raise pending_error
    return results


def reconcile_symbol_ranges():
    summaries = []
    with engine.begin() as conn:
        tables = conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = DATABASE() AND table_name LIKE 'ohlc\\_%'"
        )).fetchall()
        for (table,) in tables:
            if table == "ohlc_page_anchor":
                continue
            parts = table.split("_")
            if len(parts) < 3:
                continue
            timeframe = parts[-1]
            if timeframe not in TIMEFRAMES:
                continue
            symbols = conn.execute(text(
                f"SELECT DISTINCT symbol FROM `{table}`"
            )).fetchall()
            for (symbol_name,) in symbols:
                stats = conn.execute(text(
                    f"SELECT COUNT(*), MIN(time), MAX(time) FROM `{table}` WHERE symbol = :symbol"
                ), {"symbol": symbol_name}).fetchone()
                actual_count = int(stats[0] or 0)
                first_ts = stats[1]
                last_ts = stats[2]
                range_row = conn.execute(text(
                    "SELECT id, server FROM symbol_ranges "
                    "WHERE symbol = :symbol AND timeframe = :timeframe LIMIT 1"
                ), {"symbol": symbol_name, "timeframe": timeframe.upper()}).fetchone()
                first_stamp = datetime.fromtimestamp(first_ts, tz=timezone.utc).replace(tzinfo=None) if first_ts else None
                last_stamp = datetime.fromtimestamp(last_ts, tz=timezone.utc).replace(tzinfo=None) if last_ts else None
                if range_row:
                    conn.execute(text(
                        "UPDATE symbol_ranges SET first_ts = :first_ts, last_ts = :last_ts, count = :count "
                        "WHERE id = :id"
                    ), {"first_ts": first_stamp, "last_ts": last_stamp, "count": actual_count, "id": range_row[0]})
                    server_name = range_row[1]
                else:
                    server_name = ""
                    symbol_server = conn.execute(text(
                        "SELECT server FROM symbols WHERE name = :name LIMIT 1"
                    ), {"name": symbol_name}).fetchone()
                    if symbol_server:
                        server_name = symbol_server[0] or ""
                    conn.execute(text(
                        "INSERT INTO symbol_ranges (server, symbol, timeframe, first_ts, last_ts, count) "
                        "VALUES (:server, :symbol, :timeframe, :first_ts, :last_ts, :count) "
                        "ON DUPLICATE KEY UPDATE first_ts = VALUES(first_ts), "
                        "last_ts = VALUES(last_ts), count = VALUES(count)"
                    ), {"server": server_name, "symbol": symbol_name, "timeframe": timeframe.upper(),
                        "first_ts": first_stamp, "last_ts": last_stamp, "count": actual_count})
                rebuild_anchors(symbol_name, timeframe, conn)
                summaries.append({"symbol": symbol_name, "timeframe": timeframe, "count": actual_count})
    return summaries
