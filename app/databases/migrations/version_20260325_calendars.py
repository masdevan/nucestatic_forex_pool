from sqlalchemy import text

def upgrade(conn):
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS calendars (
            id INT AUTO_INCREMENT PRIMARY KEY,
            time DATETIME NOT NULL,
            currency VARCHAR(10),
            event VARCHAR(500),
            url VARCHAR(500),
            impact VARCHAR(20),
            actual VARCHAR(50),
            forecast VARCHAR(50),
            previous VARCHAR(50),
            description TEXT,
            description_status TINYINT(1) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """))

def downgrade(conn):
    conn.execute(text("DROP TABLE IF EXISTS calendars"))