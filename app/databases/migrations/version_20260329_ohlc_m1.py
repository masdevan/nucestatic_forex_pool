from sqlalchemy import text

def upgrade(conn):
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ohlc_m1 (
            id INT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(50),
            open DECIMAL(15, 6),
            high DECIMAL(15, 6),
            low DECIMAL(15, 6),
            close DECIMAL(15, 6),
            time BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_ohlc_m1 (symbol, time)
        )
    """))

def downgrade(conn):
    conn.execute(text("DROP TABLE IF EXISTS ohlc_m1"))
