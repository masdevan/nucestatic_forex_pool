import sys
import MetaTrader5 as mt5
from sqlalchemy import text
from app.api.models.configs.mt5_config import TIMEFRAME_MAP, init_mt5, shutdown_mt5
from app.databases.config import engine

TIMEFRAMES = ["m1", "m5", "m15", "m30", "h1", "h4", "d1", "w1", "mn1"]
TIMEFRAME_LABELS = ["M1", "M5", "M15", "M30", "H1", "H4", "D1", "W1", "MN1"]
MT5_BATCH = 50000
DB_BATCH = 1000


def get_all_table_status():
    all_tfs = "|".join(TIMEFRAMES)
    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = DATABASE() AND table_name LIKE 'ohlc_%_'"
            f"AND SUBSTRING_INDEX(SUBSTRING_INDEX(table_name, '_', -1), '_', 1) IN ({','.join(f'{chr(39)}{t}{chr(39)}' for t in TIMEFRAMES)})"
        )).fetchall()
    tables = [r[0] for r in rows]

    status = {}
    for table_name in tables:
        parts = table_name.rsplit("_", 1)
        if len(parts) != 2:
            continue
        symbol = parts[0].replace("ohlc_", "", 1)
        tf = parts[1]
        if symbol not in status:
            status[symbol] = {}
        with engine.connect() as conn:
            count = conn.execute(text(f"SELECT COUNT(*) FROM `{table_name}`")).scalar()
        status[symbol][tf] = count or 0
    return status


def get_symbols_from_db():
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT name, server FROM symbols ORDER BY name ASC")).fetchall()
    return [(r[0], r[1]) for r in rows]


def display_symbols(symbols, status):
    header = f"{'#':>4}  {'Symbol':<24}"
    for tf in TIMEFRAME_LABELS:
        header += f" {tf:>4}"
    print(f"\n{header}")
    print("-" * 68)
    for i, (sym_name, server) in enumerate(symbols, 1):
        key = sym_name.lower()
        sym_status = status.get(key, {})
        marks = ""
        for tf in TIMEFRAMES:
            count = sym_status.get(tf, 0)
            marks += f" {'✓' if count > 0 else '✗':>3}"
        print(f"{i:>4}  {sym_name:<24}{marks}")


def display_timeframes():
    print("\nTimeframes:")
    for i, tf in enumerate(TIMEFRAME_LABELS, 1):
        print(f"  {i}. {tf}")


def pick_symbol(symbols):
    raw = input("Pick symbol #: ").strip()
    if not raw.isdigit():
        print("Invalid input.")
        return None
    idx = int(raw) - 1
    if idx < 0 or idx >= len(symbols):
        print("Out of range.")
        return None
    return symbols[idx][0]


def pick_timeframe():
    raw = input("Pick timeframe #: ").strip()
    if not raw.isdigit():
        print("Invalid input.")
        return None
    idx = int(raw) - 1
    if idx < 0 or idx >= len(TIMEFRAMES):
        print("Out of range.")
        return None
    return TIMEFRAMES[idx]


def pick_timeframes_multi():
    raw = input("Pick timeframes (comma-separated, e.g. 1,3,5): ").strip()
    if not raw:
        return None
    result = []
    for part in raw.split(","):
        part = part.strip()
        if not part.isdigit():
            continue
        idx = int(part) - 1
        if 0 <= idx < len(TIMEFRAMES):
            result.append(TIMEFRAMES[idx])
    return result if result else None


def count_available(symbol, tf):
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


def seed_single(symbol, tf_key):
    table_name = f"ohlc_{symbol.lower()}_{tf_key}"
    tf_mt5 = TIMEFRAME_MAP[tf_key]

    with engine.begin() as conn:
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS `{table_name}` (
                id INT AUTO_INCREMENT PRIMARY KEY,
                symbol VARCHAR(50),
                open DECIMAL(15, 6),
                high DECIMAL(15, 6),
                low DECIMAL(15, 6),
                close DECIMAL(15, 6),
                time BIGINT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_{table_name} (symbol, time)
            )
        """))
        conn.execute(text(f"DELETE FROM `{table_name}`"))

    total = count_available(symbol, tf_mt5)
    if total == 0:
        print(f"  {tf_key.upper():>4}: {'no data':>12}")
        return 0

    inserted = 0
    offset = 0
    while offset < total:
        batch = min(MT5_BATCH, total - offset)
        rates = mt5.copy_rates_from_pos(symbol, tf_mt5, offset, batch)
        if rates is None or len(rates) == 0:
            break

        rows = []
        for rate in rates:
            rows.append({
                "symbol": symbol,
                "open": float(rate[1]),
                "high": float(rate[2]),
                "low": float(rate[3]),
                "close": float(rate[4]),
                "time": int(rate[0]),
            })

        with engine.begin() as conn:
            for i in range(0, len(rows), DB_BATCH):
                chunk = rows[i:i + DB_BATCH]
                conn.execute(
                    text(f"INSERT INTO `{table_name}` (symbol, open, high, low, close, time) "
                         "VALUES (:symbol, :open, :high, :low, :close, :time)"),
                    chunk,
                )

        inserted += len(rates)
        offset += batch
        pct = inserted * 100 // total
        print(f"\r  {tf_key.upper():>4}: {inserted:>10,} / {total:,} ({pct}%)", end="", flush=True)

    print(f"\r  {tf_key.upper():>4}: {inserted:>10,} / {total:,} ✓      ")
    return inserted


def mode_single_tf(symbols, status):
    symbol = pick_symbol(symbols)
    if not symbol:
        return
    display_timeframes()
    tf = pick_timeframe()
    if not tf:
        return
    print(f"\nSeeding {symbol} ({tf.upper()})...")
    seed_single(symbol, tf)
    status = get_all_table_status()
    display_symbols(symbols, status)


def mode_single_symbol_all_tf(symbols, status):
    symbol = pick_symbol(symbols)
    if not symbol:
        return
    print(f"\nSeeding {symbol}...")
    total = 0
    for tf in TIMEFRAMES:
        total += seed_single(symbol, tf)
    print(f"  {symbol} complete ({total:,} total bars)")
    status = get_all_table_status()
    display_symbols(symbols, status)


def mode_unseeded(symbols, status):
    to_seed = []
    for sym_name, server in symbols:
        key = sym_name.lower()
        sym_status = status.get(key, {})
        unseeded_tfs = [tf for tf in TIMEFRAMES if sym_status.get(tf, 0) == 0]
        if unseeded_tfs:
            to_seed.append((sym_name, unseeded_tfs))

    if not to_seed:
        print("All symbols already seeded.")
        return

    print(f"\n{len(to_seed)} symbols with unseeded timeframes:")
    for sym_name, tfs in to_seed:
        print(f"  {sym_name}: {', '.join(t.upper() for t in tfs)}")

    confirm = input("\nSeed these? (y/n): ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    for i, (sym_name, tfs) in enumerate(to_seed, 1):
        print(f"\n[{i}/{len(to_seed)}] Seeding {sym_name}...")
        total = 0
        for tf in tfs:
            total += seed_single(sym_name, tf)
        print(f"  {sym_name} complete ({total:,} total bars)")

    status = get_all_table_status()
    display_symbols(symbols, status)


def mode_fresh(symbols, status):
    confirm = input(f"Seed ALL {len(symbols)} symbols, ALL timeframes? (y/n): ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    for i, (sym_name, server) in enumerate(symbols, 1):
        print(f"\n[{i}/{len(symbols)}] Seeding {sym_name}...")
        total = 0
        for tf in TIMEFRAMES:
            total += seed_single(sym_name, tf)
        print(f"  {sym_name} complete ({total:,} total bars)")

    status = get_all_table_status()
    display_symbols(symbols, status)


def main():
    if not init_mt5():
        print("MT5 initialize failed")
        sys.exit(1)

    account = mt5.account_info()
    server = account.server if account else "Unknown"
    print(f"MT5 connected ({server})")

    symbols = get_symbols_from_db()
    status = get_all_table_status()
    display_symbols(symbols, status)

    shutdown_mt5()

    print(f"""
Seed modes:
  1. Single symbol, single timeframe
  2. Single symbol, all timeframes
  3. All unseeded timeframes
  4. Fresh (all symbols, all timeframes)
""")

    choice = input("Select mode (1-4): ").strip()

    if not init_mt5():
        print("MT5 initialize failed")
        sys.exit(1)

    if choice == "1":
        mode_single_tf(symbols, status)
    elif choice == "2":
        mode_single_symbol_all_tf(symbols, status)
    elif choice == "3":
        mode_unseeded(symbols, status)
    elif choice == "4":
        mode_fresh(symbols, status)
    else:
        print("Invalid choice.")

    shutdown_mt5()
    print("\nDone.")


if __name__ == "__main__":
    main()
