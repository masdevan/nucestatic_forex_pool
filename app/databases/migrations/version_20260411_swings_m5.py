from sqlalchemy import text

def upgrade(conn):
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS swings_m5 (
            id INT AUTO_INCREMENT PRIMARY KEY,
            symbol VARCHAR(50),
            type VARCHAR(20),
            price DECIMAL(15, 6),
            timestamp DATETIME,
            strength DECIMAL(10,2) DEFAULT 0,
            distance DECIMAL(15,6) DEFAULT 0,
            is_confirmed TINYINT(1) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))

def downgrade(conn):
    conn.execute(text("DROP TABLE IF EXISTS swings_m5"))