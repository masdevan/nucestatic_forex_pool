from sqlalchemy import text

def upgrade(conn):
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS market_structure_m1 (
            id INT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(50),
            timeframe VARCHAR(10),
            structure_type VARCHAR(10),
            label VARCHAR(50),
            is_break_structure TINYINT(1) DEFAULT 0,
            previous_swing_high_price DECIMAL(15, 6),
            previous_swing_high_time DATETIME,
            current_swing_high_price DECIMAL(15, 6),
            current_swing_high_time DATETIME,
            previous_swing_low_price DECIMAL(15, 6),
            previous_swing_low_time DATETIME,
            current_swing_low_price DECIMAL(15, 6),
            current_swing_low_time DATETIME,
            duration_seconds INT,
            trend_bias VARCHAR(20),
            continuation TINYINT(1) DEFAULT 0,
            speed VARCHAR(20),
            move_size DECIMAL(10,1),
            liquidity_sweep VARCHAR(10),
            max_sweep_strength DECIMAL(10,2) DEFAULT 0,
            sweep_high_count INT DEFAULT 0,
            sweep_low_count INT DEFAULT 0,
            structure_key VARCHAR(150),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uq_m1 (symbol, timeframe, structure_type, previous_swing_high_time, current_swing_high_time, previous_swing_low_time, current_swing_low_time)
        )
    """))

def downgrade(conn):
    conn.execute(text("DROP TABLE IF EXISTS market_structure_m1"))