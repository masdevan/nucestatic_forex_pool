from sqlalchemy import text
from app.databases.seeders.anchor_seeder import rebuild_anchors


def upgrade(conn):
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS ohlc_page_anchor (
            symbol VARCHAR(32) NOT NULL,
            timeframe VARCHAR(10) NOT NULL,
            k INT NOT NULL,
            start_time INT NOT NULL,
            PRIMARY KEY (symbol, timeframe, k) 
        )
    """))
    pairs = conn.execute(text(
        "SELECT symbol, timeframe FROM symbol_ranges WHERE count > 0"
    )).fetchall()
    for symbol, timeframe in pairs:
        rebuild_anchors(symbol, timeframe, conn)


def downgrade(conn):
    conn.execute(text("DROP TABLE IF EXISTS ohlc_page_anchor"))