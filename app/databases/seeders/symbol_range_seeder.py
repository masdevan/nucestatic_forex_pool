import sys
import MetaTrader5 as mt5
from sqlalchemy import text
from app.api.models.configs.mt5_config import TIMEFRAME_MAP, init_mt5, shutdown_mt5
from app.databases.config import engine

TIMEFRAMES = list(TIMEFRAME_MAP.keys())


def get_symbols_from_db():
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT name, server FROM symbols ORDER BY name ASC")).fetchall()
    return [(r[0], r[1]) for r in rows]


def _get_seeded_symbols():
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT DISTINCT symbol FROM symbol_ranges")).fetchall()
    return {r[0] for r in rows}


def display_symbols(symbols, seeded):
    print(f"\n{'#':>4}  {'Symbol':<24} {'Status':>6}")
    print("-" * 36)
    for i, (sym_name, server) in enumerate(symbols, 1):
        mark = "✓" if sym_name in seeded else "✗"
        print(f"{i:>4}  {sym_name:<24} {mark:>6}")


def pick_range(symbols):
    raw_start = input("Start symbol #: ").strip()
    raw_end = input("End symbol #: ").strip()
    if not raw_start.isdigit() or not raw_end.isdigit():
        print("Invalid input.")
        return None
    start = int(raw_start) - 1
    end = int(raw_end)
    if start < 0 or end > len(symbols) or start >= end:
        print("Invalid range.")
        return None
    return symbols[start:end]


def seed_single(symbol, server, seeded):
    if symbol in seeded:
        return
    print(f"\n  {symbol} ({server})")
    with engine.begin() as conn:
        for tf_key, tf in TIMEFRAME_MAP.items():
            total = _count_available(symbol, tf)
            if total == 0:
                print(f"    {tf_key.upper():>4}: {'no data':>12}")
                continue
            first = mt5.copy_rates_from_pos(symbol, tf, total - 1, 1)
            last = mt5.copy_rates_from_pos(symbol, tf, 0, 1)
            if first is None or last is None:
                print(f"    {tf_key.upper():>4}: {'no data':>12}")
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
            print(f"    {tf_key.upper():>4}: {total:>10,} bars → ✓")


def mode_all(symbols, seeded):
    to_seed = [(s, sv) for s, sv in symbols if s not in seeded]
    if not to_seed:
        print("All symbols already seeded.")
        return

    print(f"\n{len(to_seed)} symbols to seed.")
    confirm = input("Seed these? (y/n): ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    for i, (sym_name, server) in enumerate(to_seed, 1):
        print(f"\n[{i}/{len(to_seed)}] {sym_name} ({server})")
        seed_single(sym_name, server, {})


def mode_range(symbols, seeded):
    selected = pick_range(symbols)
    if not selected:
        return

    to_seed = [(s, sv) for s, sv in selected if s not in seeded]
    if not to_seed:
        print("All selected symbols already seeded.")
        return

    print(f"\n{len(to_seed)} symbols selected ({to_seed[0][0]} → {to_seed[-1][0]})")
    confirm = input("Seed these? (y/n): ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    for i, (sym_name, server) in enumerate(to_seed, 1):
        print(f"\n[{i}/{len(to_seed)}] {sym_name} ({server})")
        seed_single(sym_name, server, {})


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


def main():
    if not init_mt5():
        print("MT5 initialize failed")
        sys.exit(1)

    account = mt5.account_info()
    server = account.server if account else "Unknown"
    print(f"MT5 connected ({server})")

    symbols = get_symbols_from_db()
    seeded = _get_seeded_symbols()
    if seeded:
        print(f"Resuming: {len(seeded)} symbols already seeded, skipping.")
    display_symbols(symbols, seeded)

    shutdown_mt5()

    print(f"""
Seed modes:
  1. All symbols (skip seeded)
  2. Range of symbols
""")

    choice = input("Select mode (1-2): ").strip()

    if not init_mt5():
        print("MT5 initialize failed")
        sys.exit(1)

    if choice == "1":
        mode_all(symbols, seeded)
    elif choice == "2":
        mode_range(symbols, seeded)
    else:
        print("Invalid choice.")

    shutdown_mt5()
    print("\nDone.")


if __name__ == "__main__":
    main()
