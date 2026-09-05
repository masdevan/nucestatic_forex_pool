import MetaTrader5 as mt5
from sqlalchemy import text
from app.api.models.configs.mt5_config import TIMEFRAME_MAP
from app.databases.config import engine

def seed_symbol_ranges(symbol_filter=None):
    if not mt5.initialize():
        print("MT5 initialize failed")
        return
    try:
        with engine.connect() as db:
            sql = "SELECT server, name FROM symbols"
            params = {}
            if symbol_filter:
                sql += " WHERE name = :sym"
                params["sym"] = symbol_filter
            symbols = db.execute(text(sql), params).fetchall()
    except Exception as e:
        print(f"Error reading symbols: {e}")
        mt5.shutdown()
        return

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM symbol_ranges"))

    for i, (server, symbol) in enumerate(symbols, 1):
        print(f"\n[{i}/{len(symbols)}] {symbol} ({server})")
        with engine.begin() as conn:
            for tf_key, tf in TIMEFRAME_MAP.items():
                total = _count_available(symbol, tf)
                if total == 0:
                    print(f"  {tf_key.upper():>4}: {'no data':>12}")
                    continue
                first = mt5.copy_rates_from_pos(symbol, tf, total - 1, 1)
                last = mt5.copy_rates_from_pos(symbol, tf, 0, 1)
                if first is None or last is None:
                    print(f"  {tf_key.upper():>4}: {'no data':>12}")
                    continue
                conn.execute(
                    text("""
                        INSERT INTO symbol_ranges (server, symbol, timeframe, first_ts, last_ts, count)
                        VALUES (:server, :symbol, :timeframe, :first_ts, :last_ts, :count)
                        ON DUPLICATE KEY UPDATE
                            first_ts = VALUES(first_ts),
                            last_ts = VALUES(last_ts),
                            count = VALUES(count)
                    """),
                    {
                        "server": server,
                        "symbol": symbol,
                        "timeframe": tf_key.upper(),
                        "first_ts": _to_dt(first[0][0]),
                        "last_ts": _to_dt(last[0][0]),
                        "count": total,
                    },
                )
                print(f"  {tf_key.upper():>4}: {total:>10,} bars → ✓")
    mt5.shutdown()
    print("Seed complete")

def _to_dt(ts):
    from datetime import datetime
    return datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%d %H:%M:%S")

def _count_available(symbol, tf):
    high = 1
    while mt5.copy_rates_from_pos(symbol, tf, high, 1) is not None:
        high *= 2
    low = high // 2
    while low < high:
        mid = (low + high + 1) // 2
        if mt5.copy_rates_from_pos(symbol, tf, mid - 1, 1) is not None:
            low = mid
        else:
            high = mid - 1
    return low

if __name__ == "__main__":
    import sys
    seed_symbol_ranges(sys.argv[1] if len(sys.argv) > 1 else None)
