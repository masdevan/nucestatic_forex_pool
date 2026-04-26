from sqlalchemy import text

def upgrade(conn):
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS positions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ticket BIGINT,
            symbol VARCHAR(50),
            type VARCHAR(20),
            volume DECIMAL(10, 2),
            price DECIMAL(10, 5),
            sl DECIMAL(10, 5),
            tp DECIMAL(10, 5),
            profit DECIMAL(15, 2),
            closed_by VARCHAR(50),
            time DATETIME,
            is_running INT DEFAULT 1 COMMENT '1=running, 0=closed, 2=pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """))

def downgrade(conn):
    conn.execute(text("DROP TABLE IF EXISTS positions"))