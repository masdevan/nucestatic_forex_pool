import os
import time
from datetime import datetime, timezone, timedelta
from sqlalchemy import text
from app.databases.config import SessionLocal

PAIRS           = [p.strip() for p in os.getenv("TRADE_PAIR", "USDJPYm").split(",") if p.strip()]
JAKARTA_TZ      = timezone(timedelta(hours=7))
SWING_LOOKBACK  = int(os.getenv("SWING_LOOKBACK", 5))
INCREMENTAL_BARS = 1000
PIP_SIZE        = float(os.getenv("PIP_SIZE", "0.01"))

TIMEFRAMES = ["M1", "M5", "M15", "H1"]

TABLE_MAP = {
    "M1":  "ohlc_m1",
    "M5":  "ohlc_m5",
    "M15": "ohlc_m15",
    "H1":  "ohlc_h1",
}

STRUCTURE_TABLE_MAP = {
    "M1":  "market_structure_m1",
    "M5":  "market_structure_m5",
    "M15": "market_structure_m15",
    "H1":  "market_structure_h1",
}

_initialized: set[str] = set()

def find_swings(data: list[dict], lookback: int = 5) -> list[dict]:
    swings = []
    n = len(data)

    for i in range(lookback, n - lookback):
        window = [j for j in range(i - lookback, i + lookback + 1) if j != i]

        is_sh = all(data[i]["high"] > data[j]["high"] for j in window)
        is_sl = all(data[i]["low"]  < data[j]["low"]  for j in window)

        if is_sh:
            swings.append({
                "type":     "high",
                "index":    i,
                "time":     data[i]["time"],
                "time_str": data[i]["time_str"],
                "price":    data[i]["high"],
            })
        elif is_sl:
            swings.append({
                "type":     "low",
                "index":    i,
                "time":     data[i]["time"],
                "time_str": data[i]["time_str"],
                "price":    data[i]["low"],
            })

    return swings

def build_structure_sequence(swings: list[dict]) -> list[dict]:
    highs = [s for s in swings if s["type"] == "high"]
    lows  = [s for s in swings if s["type"] == "low"]

    structures = []

    for i in range(1, len(highs)):
        prev_h = highs[i - 1]
        curr_h = highs[i]

        st    = "HH" if curr_h["price"] > prev_h["price"] else "LH"
        label = "Higher High" if st == "HH" else "Lower High"

        ref_lows = [l for l in lows if l["time"] < curr_h["time"]]
        prev_l   = ref_lows[-2] if len(ref_lows) >= 2 else (ref_lows[-1] if ref_lows else None)
        curr_l   = ref_lows[-1] if ref_lows else None

        duration = curr_h["time"] - prev_h["time"]
        trend    = "bullish" if st == "HH" else "bearish"

        structures.append({
            "structure_type": st,
            "label":          label,
            "is_break":       st == "HH",
            "trend":          trend,
            "duration":       duration,
            "speed":          "fast" if duration < 3600 else "slow",
            "prev_high":      prev_h,
            "curr_high":      curr_h,
            "prev_low":       prev_l,
            "curr_low":       curr_l,
            "sort_time":      curr_h["time"],
            "_key":           f"H|{prev_h['time_str']}|{curr_h['time_str']}",
        })

    for i in range(1, len(lows)):
        prev_l = lows[i - 1]
        curr_l = lows[i]

        st    = "HL" if curr_l["price"] > prev_l["price"] else "LL"
        label = "Higher Low" if st == "HL" else "Lower Low"

        ref_highs = [h for h in highs if h["time"] < curr_l["time"]]
        prev_h    = ref_highs[-2] if len(ref_highs) >= 2 else (ref_highs[-1] if ref_highs else None)
        curr_h    = ref_highs[-1] if ref_highs else None

        duration = curr_l["time"] - prev_l["time"]
        trend    = "bullish" if st == "HL" else "bearish"

        structures.append({
            "structure_type": st,
            "label":          label,
            "is_break":       st == "LL",
            "trend":          trend,
            "duration":       duration,
            "speed":          "fast" if duration < 3600 else "slow",
            "prev_high":      prev_h,
            "curr_high":      curr_h,
            "prev_low":       prev_l,
            "curr_low":       curr_l,
            "sort_time":      curr_l["time"],
            "_key":           f"L|{prev_l['time_str']}|{curr_l['time_str']}",
        })

    structures.sort(key=lambda s: s["sort_time"])
    return structures

def load_existing_keys(db, structure_table: str, symbol: str) -> set[str]:
    try:
        rows = db.execute(text(f"""
            SELECT
                structure_type,
                previous_swing_high_time,
                current_swing_high_time,
                previous_swing_low_time,
                current_swing_low_time
            FROM {structure_table}
            WHERE symbol = :symbol
        """), {"symbol": symbol}).fetchall()

        keys = set()
        for row in rows:
            st, ph_time, ch_time, pl_time, cl_time = row

            def fmt(t):
                if t is None:
                    return None
                return t if isinstance(t, str) else str(t)

            if st in ("HH", "LH") and ph_time and ch_time:
                keys.add(f"H|{fmt(ph_time)}|{fmt(ch_time)}")
            elif st in ("HL", "LL") and pl_time and cl_time:
                keys.add(f"L|{fmt(pl_time)}|{fmt(cl_time)}")

        return keys
    except Exception as e:
        print(f"  [warn] load_existing_keys error: {e}")
        return set()

def get_last_structure_time(db, structure_table: str, symbol: str):
    try:
        row = db.execute(text(f"""
            SELECT MAX(GREATEST(
                COALESCE(current_swing_high_time, '1970-01-01'),
                COALESCE(current_swing_low_time,  '1970-01-01')
            ))
            FROM {structure_table}
            WHERE symbol = :symbol
        """), {"symbol": symbol}).fetchone()
        return row[0] if row and row[0] else None
    except Exception:
        return None

def fetch_ohlc(db, ohlc_table: str, symbol: str, limit: int | None) -> list[dict]:
    if limit:
        rows = db.execute(text(f"""
            SELECT time, time_str, open, high, low, close, tick_volume, sweep_high, sweep_low, sweep_strength
            FROM   {ohlc_table}
            WHERE  symbol = :symbol
            ORDER  BY time DESC
            LIMIT  :limit
        """), {"symbol": symbol, "limit": limit}).fetchall()
        rows = list(reversed(rows))
    else:
        rows = db.execute(text(f"""
            SELECT time, time_str, open, high, low, close, tick_volume, sweep_high, sweep_low, sweep_strength
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
            "sweep_high":  row[7],
            "sweep_low":   row[8],
            "sweep_strength": float(row[9]) if row[9] else 0.0,
        }
        for row in rows
    ]

def analyze_liquidity_for_structure(s, data):
    prev_high = s.get("prev_high")
    prev_low = s.get("prev_low")
    curr_high = s.get("curr_high")
    curr_low = s.get("curr_low")
    
    start_time = 0
    if prev_high and prev_high.get("time"):
        start_time = prev_high.get("time")
    elif prev_low and prev_low.get("time"):
        start_time = prev_low.get("time")
    
    end_time = 0
    if curr_high and curr_high.get("time"):
        end_time = curr_high.get("time")
    elif curr_low and curr_low.get("time"):
        end_time = curr_low.get("time")
    
    if start_time == 0 or end_time == 0:
        return None, 0.0, 0, 0
    
    relevant_bars = [b for b in data if start_time <= b["time"] <= end_time]
    
    if not relevant_bars:
        return None, 0.0, 0, 0
    
    high_sweeps = [b for b in relevant_bars if b.get("sweep_high") == 1]
    low_sweeps = [b for b in relevant_bars if b.get("sweep_low") == 1]
    
    sweep_count = len(high_sweeps) + len(low_sweeps)
    
    if sweep_count == 0:
        return None, 0.0, 0, 0
    
    all_sweeps = high_sweeps + low_sweeps
    max_strength = max((b.get("sweep_strength", 0) or 0 for b in all_sweeps), default=0.0)
    
    if len(high_sweeps) > len(low_sweeps):
        liquidity_sweep = "high"
    elif len(low_sweeps) > len(high_sweeps):
        liquidity_sweep = "low"
    else:
        liquidity_sweep = None
    
    return liquidity_sweep, round(max_strength, 2), len(high_sweeps), len(low_sweeps)

def save_structures(db, structure_table: str, tf_name: str, symbol: str, structures: list[dict], existing_keys: set[str], ohlc_data: list[dict]) -> int:
    saved = 0
    for s in structures:
        if s["_key"] in existing_keys:
            continue

        ph = s["prev_high"]
        ch = s["curr_high"]
        pl = s["prev_low"]
        cl = s["curr_low"]

        if s["structure_type"] in ("HH", "LH"):
            move_size = round(abs(ch["price"] - ph["price"]) / PIP_SIZE, 1) if ph and ch else None
        else:
            move_size = round(abs(cl["price"] - pl["price"]) / PIP_SIZE, 1) if pl and cl else None

        liquidity_sweep, max_sweep_strength, sweep_high_count, sweep_low_count = analyze_liquidity_for_structure(s, ohlc_data)

        db.execute(text(f"""
            INSERT IGNORE INTO {structure_table} (
                symbol, timeframe, structure_type, label, is_break_structure,
                previous_swing_high_price, previous_swing_high_time,
                current_swing_high_price,  current_swing_high_time,
                previous_swing_low_price,  previous_swing_low_time,
                current_swing_low_price,   current_swing_low_time,
                duration_seconds, trend_bias, continuation, speed, move_size,
                liquidity_sweep, max_sweep_strength, sweep_high_count, sweep_low_count,
                structure_key
            ) VALUES (
                :symbol, :tf, :st, :label, :is_break,
                :ph_price, :ph_time,
                :ch_price, :ch_time,
                :pl_price, :pl_time,
                :cl_price, :cl_time,
                :duration, :trend, :cont, :speed, :move_size,
                :lq_sweep, :max_sweep, :sweep_high_cnt, :sweep_low_cnt,
                :key
            )
        """), {
            "symbol":   symbol,
            "tf":       tf_name,
            "st":       s["structure_type"],
            "label":    s["label"],
            "is_break": 1 if s["is_break"] else 0,
            "ph_price": float(ph["price"]) if ph else None,
            "ph_time":  ph["time_str"]     if ph else None,
            "ch_price": float(ch["price"]) if ch else None,
            "ch_time":  ch["time_str"]     if ch else None,
            "pl_price": float(pl["price"]) if pl else None,
            "pl_time":  pl["time_str"]     if pl else None,
            "cl_price": float(cl["price"]) if cl else None,
            "cl_time":  cl["time_str"]     if cl else None,
            "duration": s["duration"],
            "trend":    s["trend"],
            "cont":     1 if s["is_break"] else 0,
            "speed":    s["speed"],
            "move_size": move_size,
            "lq_sweep": liquidity_sweep,
            "max_sweep": max_sweep_strength,
            "sweep_high_cnt": sweep_high_count,
            "sweep_low_cnt": sweep_low_count,
            "key":      s["_key"],
        })

        existing_keys.add(s["_key"])
        saved += 1
        
        if tf_name not in _initialized:
            print(f"  + [{s['structure_type']}] {s['label']} | {s['trend']} | {s['_key']}")

    if saved:
        db.commit()

    return saved

def analyze_timeframe(tf_name: str, symbol: str, db) -> int:
    ohlc_table      = TABLE_MAP[tf_name]
    structure_table = STRUCTURE_TABLE_MAP[tf_name]
    is_first_run    = f"{symbol}:{tf_name}" not in _initialized

    min_bars = SWING_LOOKBACK * 2 + 5
    limit    = None if is_first_run else INCREMENTAL_BARS

    data = fetch_ohlc(db, ohlc_table, symbol, limit)

    if len(data) < min_bars:
        if is_first_run:
            print(f"[{tf_name}] Not enough data ({len(data)} bars, minimum {min_bars})")
        return 0

    if is_first_run:
        mode = "FULL SCAN"
        print(f"[{tf_name}] [{mode}] {len(data)} bars loaded")

    swings = find_swings(data, lookback=SWING_LOOKBACK)
    n_high = sum(1 for s in swings if s["type"] == "high")
    n_low  = sum(1 for s in swings if s["type"] == "low")
    
    if is_first_run:
        print(f"[{tf_name}] {len(swings)} swings found ({n_high}H {n_low}L)")

    if n_high < 2 and n_low < 2:
        if is_first_run:
            print(f"[{tf_name}] Not enough swings for structure detection")
        return 0

    structures    = build_structure_sequence(swings)
    existing_keys = load_existing_keys(db, structure_table, symbol)
    
    if is_first_run:
        print(f"[{symbol}][{tf_name}] {len(structures)} structures detected | {len(existing_keys)} existing")

    saved = save_structures(db, structure_table, tf_name, symbol, structures, existing_keys, data)

    if saved > 0:
        if is_first_run:
            print(f"[{symbol}][{tf_name}] {saved} new structure(s) saved")
        else:
            print(f"[{symbol}][{tf_name}] +{saved} new")

    if is_first_run:
        _initialized.add(f"{symbol}:{tf_name}")

    return saved


def run_job():
    print(f"[{datetime.now()}] Market structure analyzer starts")
    print(f"Pairs            : {PAIRS}")
    print(f"Swing lookback   : {SWING_LOOKBACK} candles")
    print(f"Incremental bars : {INCREMENTAL_BARS}")
    print(f"Timeframes       : {', '.join(TIMEFRAMES)}")

    db = SessionLocal()
    try:
        for pair in PAIRS:
            row = db.execute(text(f"SELECT COUNT(*) FROM market_structure_m1 WHERE symbol = :symbol"), {"symbol": pair}).fetchone()
            has_data = row and row[0] > 100
            if has_data:
                print(f"[{pair}] Data already exists, entering live mode")
                for tf in TIMEFRAMES:
                    _initialized.add(f"{pair}:{tf}")
            else:
                print(f"[{pair}] Database empty, performing full initial scan")
    finally:
        db.close()

    print()
    
    cycle_count = 0

    while True:
        cycle_count += 1
        try:
            db = SessionLocal()
            try:
                for pair in PAIRS:
                    for tf in TIMEFRAMES:
                        try:
                            analyze_timeframe(tf, pair, db)
                        except Exception as e:
                            print(f"[{pair}][{tf}] Error: {e}")
                        time.sleep(0.1)
            finally:
                db.close()

            print(f"[{datetime.now().strftime('%H:%M:%S')}] Cycle #{cycle_count} complete")
            time.sleep(5)

        except Exception as e:
            print(f"Loop error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_job()