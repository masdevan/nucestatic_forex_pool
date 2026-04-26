import os
import time
from datetime import datetime, timezone, timedelta
from sqlalchemy import text
from app.databases.config import SessionLocal

PAIRS            = [p.strip() for p in os.getenv("TRADE_PAIR", "USDJPYm").split(",") if p.strip()]
JAKARTA_TZ       = timezone(timedelta(hours=7))
SWING_LOOKBACK   = int(os.getenv("SWING_LOOKBACK", 5))
INCREMENTAL_BARS = 1000
LIVE_MODE_THRESHOLD = 100 

TIMEFRAMES = ["M1", "M5", "M15", "H1"]

TABLE_MAP = {
    "M1":  "ohlc_m1",
    "M5":  "ohlc_m5",
    "M15": "ohlc_m15",
    "H1":  "ohlc_h1",
}

SWINGS_TABLE_MAP = {
    "M1":  "swings_m1",
    "M5":  "swings_m5",
    "M15": "swings_m15",
    "H1":  "swings_h1",
}

_initialized: set[str] = set()

def calculate_atr(data: list[dict], period: int = 14) -> float:
    if len(data) < 2:
        return 1.0

    true_ranges = []
    for i in range(1, len(data)):
        high       = data[i]["high"]
        low        = data[i]["low"]
        prev_close = data[i - 1]["close"]
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        true_ranges.append(tr)

    recent = true_ranges[-period:] if len(true_ranges) >= period else true_ranges
    return sum(recent) / len(recent) if recent else 1.0

def calculate_strength(data: list[dict], index: int, lookback: int, atr: float) -> float:
    if atr == 0:
        return 0.0

    candle     = data[index]
    window_idx = [j for j in range(index - lookback, index + lookback + 1) if j != index]

    avg_high = sum(data[j]["high"] for j in window_idx) / len(window_idx)
    avg_low  = sum(data[j]["low"]  for j in window_idx) / len(window_idx)

    proj_high  = (candle["high"] - avg_high) / atr
    proj_low   = (avg_low - candle["low"])   / atr
    proj_ratio = max(proj_high, proj_low)

    strength = min(proj_ratio * 10.0, 10.0)
    strength = max(strength, 0.0)

    return round(strength, 2)

def is_swing_confirmed(data: list[dict], index: int, swing_type: str, lookback: int) -> bool:
    candle       = data[index]
    post_candles = data[index + 1 : index + 1 + lookback]

    if len(post_candles) < lookback:
        return False

    if swing_type == "swing_high":
        return sum(1 for c in post_candles if c["low"] < candle["low"]) >= 2
    elif swing_type == "swing_low":
        return sum(1 for c in post_candles if c["high"] > candle["high"]) >= 2

    return False

def filter_alternating_swings(swings: list[dict]) -> list[dict]:
    if not swings:
        return []

    result = [swings[0]]

    for current in swings[1:]:
        last = result[-1]

        if current["type"] == last["type"]:
            if current["type"] == "swing_high" and current["price"] > last["price"]:
                result[-1] = current
            elif current["type"] == "swing_low" and current["price"] < last["price"]:
                result[-1] = current
        else:
            result.append(current)

    return result

def find_swings(data: list[dict], lookback: int = 5) -> list[dict]:
    swings = []
    n      = len(data)
    atr    = calculate_atr(data)

    for i in range(lookback, n - lookback):
        window = [j for j in range(i - lookback, i + lookback + 1) if j != i]

        is_sh = all(data[i]["high"] > data[j]["high"] for j in window)
        is_sl = all(data[i]["low"]  < data[j]["low"]  for j in window)

        if is_sh:
            confirmed = is_swing_confirmed(data, i, "swing_high", lookback)
            strength  = calculate_strength(data, i, lookback, atr)
            swings.append({
                "type":         "swing_high",
                "time":         data[i]["time"],
                "time_str":     data[i]["time_str"],
                "price":        data[i]["high"],
                "strength":     strength,
                "distance":     None,
                "is_confirmed": confirmed,
            })

        elif is_sl:
            confirmed = is_swing_confirmed(data, i, "swing_low", lookback)
            strength  = calculate_strength(data, i, lookback, atr)
            swings.append({
                "type":         "swing_low",
                "time":         data[i]["time"],
                "time_str":     data[i]["time_str"],
                "price":        data[i]["low"],
                "strength":     strength,
                "distance":     None,
                "is_confirmed": confirmed,
            })

    return filter_alternating_swings(swings)

def count_existing_swings(db, swings_table: str, symbol: str) -> int:
    try:
        return db.execute(text(f"""
            SELECT COUNT(*) FROM {swings_table} WHERE symbol = :symbol
        """), {"symbol": symbol}).scalar() or 0
    except Exception:
        return 0

def load_existing_swings(db, swings_table: str, symbol: str) -> dict[str, dict]:
    try:
        rows = db.execute(text(f"""
            SELECT id, type, timestamp, is_confirmed, strength
            FROM   {swings_table}
            WHERE  symbol = :symbol
        """), {"symbol": symbol}).fetchall()

        return {
            f"{row[1]}|{row[2]}": {
                "id":           row[0],
                "is_confirmed": row[3],
                "strength":     row[4],
            }
            for row in rows
        }
    except Exception as e:
        print(f"  [warn] load_existing_swings error: {e}")
        return {}

def fetch_ohlc(db, ohlc_table: str, symbol: str, limit: int | None) -> list[dict]:
    if limit:
        rows = db.execute(text(f"""
            SELECT time, time_str, open, high, low, close, tick_volume
            FROM   {ohlc_table}
            WHERE  symbol = :symbol
            ORDER  BY time DESC
            LIMIT  :limit
        """), {"symbol": symbol, "limit": limit}).fetchall()
        rows = list(reversed(rows))
    else:
        rows = db.execute(text(f"""
            SELECT time, time_str, open, high, low, close, tick_volume
            FROM   {ohlc_table}
            WHERE  symbol = :symbol
            ORDER  BY time ASC
        """), {"symbol": symbol}).fetchall()

    return [
        {
            "time":        row[0],
            "time_str":    row[1],
            "open":        float(row[2]),
            "high":        float(row[3]),
            "low":         float(row[4]),
            "close":       float(row[5]),
            "tick_volume": row[6],
        }
        for row in rows
    ]

def get_valid_keys(swings: list[dict]) -> set[str]:
    return {f"{s['type']}|{s['time_str']}" for s in swings}

def save_swings(
    db,
    swings_table: str,
    tf_name: str,
    symbol: str,
    swings: list[dict],
    existing_swings: dict[str, dict],
    min_time: str | None = None,
    verbose: bool = True,     
) -> tuple[int, int, int]:
    inserted   = 0
    updated    = 0
    deleted    = 0
    prev_price = None

    valid_keys = get_valid_keys(swings)

    for key, existing in list(existing_swings.items()):
        if key not in valid_keys:
            swing_type, ts = key.split("|", 1)

            if min_time is not None and ts < min_time:
                continue

            db.execute(text(f"""
                DELETE FROM {swings_table}
                WHERE  symbol = :symbol
                  AND  type   = :type
                  AND  timestamp = :ts
            """), {"symbol": symbol, "type": swing_type, "ts": ts})
            del existing_swings[key]
            deleted += 1

            if verbose:
                print(f"  - [{swing_type:10s}] removed  {ts}")

    for s in swings:
        key        = f"{s['type']}|{s['time_str']}"
        distance   = abs(s["price"] - prev_price) if prev_price is not None else 0.0
        prev_price = s["price"]

        if key not in existing_swings:
            db.execute(text(f"""
                INSERT INTO {swings_table} (
                    symbol, type, price, timestamp, strength, distance, is_confirmed
                ) VALUES (
                    :symbol, :type, :price, :ts, :strength, :distance, :is_confirmed
                )
            """), {
                "symbol":       symbol,
                "type":         s["type"],
                "price":        s["price"],
                "ts":           s["time_str"],
                "strength":     s["strength"],
                "distance":     distance,
                "is_confirmed": int(s["is_confirmed"]),
            })
            existing_swings[key] = {
                "id":           None,
                "is_confirmed": int(s["is_confirmed"]),
                "strength":     s["strength"],
            }
            inserted += 1

            if verbose:
                status = "CONFIRMED" if s["is_confirmed"] else "unconfirmed"
                print(f"  + [{s['type']:10s}] {s['price']:.5f}  str={s['strength']:.2f}  [{status}]  {s['time_str']}")

        else:
            existing      = existing_swings[key]
            new_confirmed = int(s["is_confirmed"])
            new_strength  = s["strength"]

            changed = (
                existing["is_confirmed"] != new_confirmed
                or abs(float(existing["strength"] or 0.0) - new_strength) > 0.01
            )

            if changed:
                db.execute(text(f"""
                    UPDATE {swings_table}
                    SET    is_confirmed = :is_confirmed,
                           strength     = :strength
                    WHERE  symbol    = :symbol
                      AND  type      = :type
                      AND  timestamp = :ts
                """), {
                    "symbol":       symbol,
                    "type":         s["type"],
                    "ts":           s["time_str"],
                    "is_confirmed": new_confirmed,
                    "strength":     new_strength,
                })
                existing_swings[key]["is_confirmed"] = new_confirmed
                existing_swings[key]["strength"]     = new_strength
                updated += 1

                if verbose:
                    old_c = "✓" if existing["is_confirmed"] else "✗"
                    new_c = "✓" if new_confirmed            else "✗"
                    print(f"  ↻ [{s['type']:10s}] {s['price']:.5f}  confirmed {old_c}→{new_c}  str={new_strength:.2f}  {s['time_str']}")

    if inserted or updated or deleted:
        db.commit()

    return inserted, updated, deleted

def analyze_timeframe(tf_name: str, symbol: str, db) -> tuple[int, int, int]:
    ohlc_table   = TABLE_MAP[tf_name]
    swings_table = SWINGS_TABLE_MAP[tf_name]
    is_first_run = f"{symbol}:{tf_name}" not in _initialized

    if is_first_run:
        db_count = count_existing_swings(db, swings_table, symbol)
        if db_count >= LIVE_MODE_THRESHOLD:
            _initialized.add(f"{symbol}:{tf_name}")
            is_first_run = False
            print(f"[{symbol}][{tf_name}] DB has {db_count} swings — skipping full scan, entering LIVE mode")

    min_bars = SWING_LOOKBACK * 2 + 5
    limit    = None if is_first_run else INCREMENTAL_BARS
    verbose  = is_first_run  

    data = fetch_ohlc(db, ohlc_table, symbol, limit)

    if len(data) < min_bars:
        print(f"[{symbol}][{tf_name}] Insufficient data ({len(data)} bars, need {min_bars})")
        return 0, 0, 0

    swings = find_swings(data, lookback=SWING_LOOKBACK)

    if is_first_run:
        n_high   = sum(1 for s in swings if s["type"] == "swing_high")
        n_low    = sum(1 for s in swings if s["type"] == "swing_low")
        n_conf   = sum(1 for s in swings if s["is_confirmed"])
        print(f"[{symbol}][{tf_name}] FULL SCAN — {len(data)} bars | {len(swings)} swings ({n_high}H {n_low}L) confirmed={n_conf}")

    existing_swings = load_existing_swings(db, swings_table, symbol)
    min_time = str(data[0]["time_str"]) if (data and not is_first_run) else None

    inserted, updated, deleted = save_swings(
        db, swings_table, tf_name, symbol, swings, existing_swings,
        min_time=min_time,
        verbose=verbose,
    )

    if is_first_run:
        print(f"[{symbol}][{tf_name}] done — {inserted} inserted, {updated} updated, {deleted} deleted")
        _initialized.add(f"{symbol}:{tf_name}")
    elif inserted or updated or deleted:
        print(f"[{symbol}][{tf_name}] [Insert: {inserted}] [Update: {updated}] [Delete: {deleted}]")

    return inserted, updated, deleted


def run_job():
    print(f"[{datetime.now(JAKARTA_TZ).strftime('%Y-%m-%d %H:%M:%S')}] Swing analyzer started")
    print(f"Pairs={PAIRS}")
    print(f"Lookback={SWING_LOOKBACK}  Incremental={INCREMENTAL_BARS}  TFs={', '.join(TIMEFRAMES)}")
    print("─" * 60)

    while True:
        try:
            db = SessionLocal()
            try:
                total_inserted = 0
                total_updated  = 0
                total_deleted  = 0

                for pair in PAIRS:
                    for tf in TIMEFRAMES:
                        try:
                            ins, upd, dlt  = analyze_timeframe(tf, pair, db)
                            total_inserted += ins
                            total_updated  += upd
                            total_deleted  += dlt
                        except Exception as e:
                            print(f"[{pair}][{tf}] Error: {e}")
                        time.sleep(0.1)

            finally:
                db.close()

            if total_inserted or total_updated or total_deleted:
                now = datetime.now(JAKARTA_TZ).strftime("%H:%M:%S")
                print(f"[{now}] cycle — [Insert: {total_inserted}] [Update: {total_updated}] [Delete: {total_deleted}]")

            time.sleep(5)

        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    run_job()