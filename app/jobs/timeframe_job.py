import os
import time
from datetime import datetime, timezone, timedelta
from sqlalchemy import text
import MetaTrader5 as mt5
from app.databases.config import SessionLocal
from app.api.configs.mt5_config import init_mt5, shutdown_mt5

HISTORY_DAYS = 365
PAIRS = [p.strip() for p in os.getenv("TRADE_PAIR", "USDJPYm").split(",") if p.strip()]
JAKARTA_TZ = timezone(timedelta(hours=7))
TIMEFRAMES = ["M1", "M5", "M15", "H1"]

TABLE_MAP = {
    "M1": "ohlc_m1",
    "M5": "ohlc_m5",
    "M15": "ohlc_m15",
    "H1": "ohlc_h1",
}

TIMEFRAME_MAP = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "H1": mt5.TIMEFRAME_H1,
}

ATR_PERIOD = 14


def calculate_atr(data, period=14):
    if len(data) < period:
        return [None] * len(data)

    atr_values = [None] * (period - 1)

    for i in range(period - 1, len(data)):
        tr_values = []
        for j in range(max(0, i - period + 1), i + 1):
            high = data[j]["high"]
            low = data[j]["low"]
            tr = high - low
            if j > 0:
                prev_close = data[j - 1]["close"]
                tr = max(tr, abs(high - prev_close), abs(low - prev_close))
            tr_values.append(tr)
        atr = sum(tr_values) / period
        atr_values.append(round(atr, 6))

    return atr_values


def get_session_from_time(ts):
    dt = datetime.fromtimestamp(ts, JAKARTA_TZ)
    hour = dt.hour
    if 6 <= hour < 14:
        return 1
    elif 14 <= hour < 19:
        return 2
    else:
        return 3


def fetch_all_rates(pair, mt5_tf, chunk_size=1000, max_candles=10000, silent=False):
    all_rates = []
    start_pos = 0

    while True:
        rates = mt5.copy_rates_from_pos(pair, mt5_tf, start_pos, chunk_size)

        if rates is None or len(rates) == 0:
            break

        all_rates.extend(rates)

        if not silent:
            print(f"[{pair}] Fetched {len(rates)} candles (total: {len(all_rates)})")

        if len(rates) < chunk_size:
            break

        start_pos += chunk_size

        if len(all_rates) >= max_candles:
            break

    return all_rates


def fetch_and_save_timeframe(pair, tf_name, is_initial=False):
    table_name = TABLE_MAP[tf_name]
    mt5_tf = TIMEFRAME_MAP[tf_name]

    symbol_info = mt5.symbol_info(pair)
    if symbol_info is None:
        mt5.symbol_select(pair, True)
        time.sleep(0.5)
        symbol_info = mt5.symbol_info(pair)
        if symbol_info is None:
            print(f"[{pair}][{tf_name}] Symbol {pair} not found")
            return 0

    try:
        if is_initial:
            print(f"[{pair}][{tf_name}] Initial sync...")
            rates = fetch_all_rates(pair, mt5_tf, silent=not is_initial)
        else:
            rates = mt5.copy_rates_from_pos(pair, mt5_tf, 0, 1000)
    except Exception as e:
        print(f"[{pair}][{tf_name}] Fetch error: {e}")
        return 0

    if rates is None or len(rates) < 2:
        return 0

    db = SessionLocal()
    saved_count = 0

    try:
        completed_rates = rates[:-1]
        current_rate = rates[-1]

        for rate in completed_rates:
            ts = int(rate[0])

            existing = db.execute(
                text(f"SELECT id, is_done FROM {table_name} WHERE symbol = :symbol AND time = :time"),
                {"symbol": pair, "time": ts}
            ).fetchone()

            if existing:
                if existing[1] == 0:
                    db.execute(text(f"""
                        UPDATE {table_name}
                        SET high = :high, low = :low, close = :close,
                            tick_volume = :tick_volume, is_done = 1
                        WHERE symbol = :symbol AND time = :time
                    """), {
                        "symbol": pair, "time": ts,
                        "high": float(rate[2]), "low": float(rate[3]),
                        "close": float(rate[4]), "tick_volume": int(rate[5])
                    })
            else:
                time_str = datetime.fromtimestamp(ts, JAKARTA_TZ).strftime("%Y-%m-%d %H:%M:%S")
                session = get_session_from_time(ts)
                db.execute(text(f"""
                    INSERT INTO {table_name}
                    (symbol, time, time_str, session, open, high, low, close,
                     tick_volume, is_done, atr, sweep_high, sweep_low, sweep_strength)
                    VALUES (:symbol, :time, :time_str, :session, :open, :high, :low, :close,
                            :tick_volume, 1, 0, 0, 0, 0)
                """), {
                    "symbol": pair, "time": ts,
                    "time_str": time_str, "session": session,
                    "open": float(rate[1]), "high": float(rate[2]),
                    "low": float(rate[3]), "close": float(rate[4]),
                    "tick_volume": int(rate[5])
                })
                saved_count += 1

        ts = int(current_rate[0])
        time_str = datetime.fromtimestamp(ts, JAKARTA_TZ).strftime("%Y-%m-%d %H:%M:%S")
        session = get_session_from_time(ts)

        existing = db.execute(
            text(f"SELECT id FROM {table_name} WHERE symbol = :symbol AND time = :time"),
            {"symbol": pair, "time": ts}
        ).fetchone()

        if existing:
            db.execute(text(f"""
                UPDATE {table_name}
                SET high = :high, low = :low, close = :close,
                    tick_volume = :tick_volume, is_done = 0
                WHERE symbol = :symbol AND time = :time
            """), {
                "symbol": pair, "time": ts,
                "high": float(current_rate[2]), "low": float(current_rate[3]),
                "close": float(current_rate[4]), "tick_volume": int(current_rate[5])
            })
        else:
            db.execute(text(f"""
                INSERT INTO {table_name}
                (symbol, time, time_str, session, open, high, low, close,
                 tick_volume, is_done, atr, sweep_high, sweep_low, sweep_strength)
                VALUES (:symbol, :time, :time_str, :session, :open, :high, :low, :close,
                        :tick_volume, 0, 0, 0, 0, 0)
            """), {
                "symbol": pair, "time": ts,
                "time_str": time_str, "session": session,
                "open": float(current_rate[1]), "high": float(current_rate[2]),
                "low": float(current_rate[3]), "close": float(current_rate[4]),
                "tick_volume": int(current_rate[5])
            })

        db.commit()

    finally:
        db.close()

    return saved_count


def update_atr_for_timeframe(pair, tf_name, is_initial=False):
    table_name = TABLE_MAP[tf_name]

    db = SessionLocal()
    try:
        rows = db.execute(text(f"""
            SELECT id, open, high, low, close, atr
            FROM {table_name}
            WHERE symbol = :symbol AND is_done = 1
            ORDER BY time ASC
        """), {"symbol": pair}).fetchall()

        if len(rows) < ATR_PERIOD:
            return

        data = [{
            "id": r[0],
            "open": float(r[1]), "high": float(r[2]),
            "low": float(r[3]), "close": float(r[4]),
            "atr": float(r[5]) if r[5] else 0.0
        } for r in rows]

        if is_initial:
            atr_values = calculate_atr(data, ATR_PERIOD)
            updates = [
                {"atr": atr_values[i], "id": data[i]["id"]}
                for i in range(len(data))
                if atr_values[i] is not None
            ]
        else:
            needs_update = [
                i for i, d in enumerate(data)
                if d["atr"] == 0.0 and i >= ATR_PERIOD - 1
            ]
            if not needs_update:
                return

            atr_values = calculate_atr(data, ATR_PERIOD)
            updates = [
                {"atr": atr_values[i], "id": data[i]["id"]}
                for i in needs_update
                if atr_values[i] is not None
            ]

        for upd in updates:
            db.execute(
                text(f"UPDATE {table_name} SET atr = :atr WHERE id = :id"),
                upd
            )
        db.commit()

        if is_initial and updates:
            print(f"[{pair}][{tf_name}] ATR updated: {len(updates)} candle(s)")

    finally:
        db.close()


def detect_liquidity_sweep(pair, tf_name, is_initial=False):
    table_name = TABLE_MAP[tf_name]

    db = SessionLocal()
    try:
        if is_initial:
            rows = db.execute(text(f"""
                SELECT id, time, open, high, low, close, tick_volume, atr
                FROM {table_name}
                WHERE symbol = :symbol AND is_done = 1
                ORDER BY time ASC
            """), {"symbol": pair}).fetchall()
        else:
            rows = db.execute(text(f"""
                SELECT id, time, open, high, low, close, tick_volume, atr
                FROM {table_name}
                WHERE symbol = :symbol AND is_done = 1
                ORDER BY time DESC
                LIMIT 20
            """), {"symbol": pair}).fetchall()
            rows = list(reversed(rows))

        if len(rows) < 3:
            return

        data = [{
            "id": r[0], "time": r[1],
            "open": float(r[2]), "high": float(r[3]),
            "low": float(r[4]), "close": float(r[5]),
            "tick_volume": r[6],
            "atr": float(r[7]) if r[7] else None
        } for r in rows]

        updates = []

        for i in range(1, len(data)):
            curr = data[i]
            prev = data[i - 1]

            if not curr["atr"] or curr["atr"] <= 0:
                continue

            sweep_high = 0
            sweep_low = 0
            sweep_strength = 0.0

            if curr["high"] > prev["high"] and curr["close"] < prev["high"]:
                wick_size = curr["high"] - max(prev["high"], curr["close"])
                sweep_strength = round(wick_size / curr["atr"], 2)
                sweep_high = 1
            elif curr["low"] < prev["low"] and curr["close"] > prev["low"]:
                wick_size = min(prev["low"], curr["close"]) - curr["low"]
                sweep_strength = round(wick_size / curr["atr"], 2)
                sweep_low = 1

            updates.append({
                "sweep_high": sweep_high,
                "sweep_low": sweep_low,
                "sweep_strength": sweep_strength,
                "id": curr["id"]
            })

        for upd in updates:
            db.execute(text(f"""
                UPDATE {table_name}
                SET sweep_high = :sweep_high,
                    sweep_low = :sweep_low,
                    sweep_strength = :sweep_strength
                WHERE id = :id
            """), upd)

        db.commit()

        sweeps_found = sum(1 for u in updates if u["sweep_high"] or u["sweep_low"])
        if is_initial and sweeps_found:
            print(f"[{pair}][{tf_name}] Liquidity sweep detected: {sweeps_found} candle(s)")

    finally:
        db.close()


def check_pair_has_data(pair):
    db = SessionLocal()
    try:
        row = db.execute(
            text("SELECT COUNT(*) FROM ohlc_m1 WHERE symbol = :symbol"),
            {"symbol": pair}
        ).fetchone()
        return row and row[0] > 1000
    finally:
        db.close()


def validate_pairs():
    valid_pairs = []
    for pair in PAIRS:
        symbol_info = mt5.symbol_info(pair)
        if symbol_info is None:
            mt5.symbol_select(pair, True)
            time.sleep(0.3)
            symbol_info = mt5.symbol_info(pair)

        if symbol_info is None:
            print(f"[WARN] Symbol {pair} not found in MT5, skipped.")
        else:
            print(f"[OK] Symbol {pair} found.")
            valid_pairs.append(pair)
    return valid_pairs


def run_job():
    if not init_mt5():
        print("MT5 initialization failed")
        return

    account_info = mt5.account_info()
    if account_info is None:
        print("Failed to get account info")
        shutdown_mt5()
        return

    print(f"MT5 connected. Account: {account_info.login}")
    print(f"Pairs from env: {PAIRS}")

    valid_pairs = validate_pairs()
    if not valid_pairs:
        print("No valid pairs available for processing. Job stopped.")
        shutdown_mt5()
        return

    print(f"Valid pairs: {valid_pairs}")

    first_run = {pair: not check_pair_has_data(pair) for pair in valid_pairs}

    for pair, is_first in first_run.items():
        status = "full initial sync" if is_first else "live mode"
        print(f"[{pair}] Status: {status}")

    while True:
        try:
            for pair in valid_pairs:
                is_initial = first_run[pair]
                for tf in TIMEFRAMES:
                    fetch_and_save_timeframe(pair, tf, is_initial=is_initial)
                    update_atr_for_timeframe(pair, tf, is_initial=is_initial)
                    detect_liquidity_sweep(pair, tf, is_initial=is_initial)

                if first_run[pair]:
                    print(f"[{pair}][{datetime.now()}] Initial sync completed, switching to live mode...")
                    first_run[pair] = False

            time.sleep(1)

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)


if __name__ == "__main__":
    run_job()