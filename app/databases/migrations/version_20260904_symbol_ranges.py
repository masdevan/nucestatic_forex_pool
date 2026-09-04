from sqlalchemy import text

def upgrade(conn):
    conn.execute(text("""
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
    """))

def downgrade(conn):
    conn.execute(text("DROP TABLE IF EXISTS symbol_ranges"))
