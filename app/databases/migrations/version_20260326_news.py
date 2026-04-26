from sqlalchemy import text

def upgrade(conn):
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS news (
            id INT AUTO_INCREMENT PRIMARY KEY,
            time DATETIME NOT NULL,
            title VARCHAR(500) NOT NULL,
            url VARCHAR(500),
            description LONGTEXT,
            description_status TINYINT(1) DEFAULT 0,
            score INT DEFAULT 0,
            pair_impact VARCHAR(255) DEFAULT "",
            direction VARCHAR(50) DEFAULT "",
            reason VARCHAR(500) DEFAULT "",
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """))

def downgrade(conn):
    conn.execute(text("DROP TABLE IF EXISTS news"))
