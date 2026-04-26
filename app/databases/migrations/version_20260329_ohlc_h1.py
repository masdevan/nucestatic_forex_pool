from sqlalchemy import text

def upgrade(conn):
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ohlc_h1 (
            id INT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(50),
            time BIGINT,
            time_str DATETIME,
            -- Session: 1=Asia(06:00-14:00), 2=London(14:00-19:00), 3=NewYork(19:00-06:00)
            session TINYINT,
            open DECIMAL(15, 6),
            high DECIMAL(15, 6),
            low DECIMAL(15, 6),
            close DECIMAL(15, 6),
            tick_volume INT,
            is_done TINYINT(1) DEFAULT 0,
            atr DECIMAL(15, 6) DEFAULT 0,
            sweep_high TINYINT(1) DEFAULT 0,
            sweep_low TINYINT(1) DEFAULT 0,
            sweep_strength DECIMAL(10, 2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_ohlc_h1 (symbol, time)
        )
    """))

def downgrade(conn):
    conn.execute(text("DROP TABLE IF EXISTS ohlc_h1"))