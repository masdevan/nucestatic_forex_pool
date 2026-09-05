from sqlalchemy import text

def upgrade(conn):
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS symbols (
            id INT AUTO_INCREMENT PRIMARY KEY,
            server VARCHAR(100) NOT NULL DEFAULT '',
            name VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_symbol_server (server, name),
            INDEX idx_name (name)
        )
    """))

def downgrade(conn):
    conn.execute(text("DROP TABLE IF EXISTS symbols"))
