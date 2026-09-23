from sqlalchemy import text

TIMEFRAMES = ["m1", "m5", "m15", "m30", "h1", "h4", "d1", "w1", "mn1"]

def upgrade(conn):
    symbols_table = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema = DATABASE() AND table_name = 'symbols'"
    )).scalar()

    if not symbols_table:
        print("Symbols table not found, skipping OHLC table creation")
        return

    result = conn.execute(text("SELECT DISTINCT name FROM symbols"))
    symbols = [row[0] for row in result.fetchall()]

    if not symbols:
        print("No symbols found, skipping OHLC table creation")
        return

    for symbol in symbols:
        table_prefix = f"ohlc_{symbol.lower()}"
        for tf in TIMEFRAMES:
            table_name = f"{table_prefix}_{tf}"
            conn.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
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
    print(f"Created OHLC tables for {len(symbols)} symbols")

def downgrade(conn):
    result = conn.execute(text("SELECT DISTINCT name FROM symbols"))
    symbols = [row[0] for row in result.fetchall()]

    for symbol in symbols:
        table_prefix = f"ohlc_{symbol.lower()}"
        for tf in TIMEFRAMES:
            conn.execute(text(f"DROP TABLE IF EXISTS {table_prefix}_{tf}"))
