import MetaTrader5 as mt5
from sqlalchemy import text
from app.databases.config import engine

def seed_symbols():
    if not mt5.initialize():
        print("MT5 initialize failed")
        return
    account = mt5.account_info()
    server = account.server if account else ""
    symbols = [s.name for s in mt5.symbols_get()] if mt5.symbols_get() else []
    mt5.shutdown()

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM symbols"))
        for name in symbols:
            conn.execute(
                text("""
                    INSERT INTO symbols (server, name) VALUES (:server, :name)
                    ON DUPLICATE KEY UPDATE server = VALUES(server)
                """),
                {"server": server, "name": name},
            )
    print(f"Seeded {len(symbols)} symbols (server: {server})")

if __name__ == "__main__":
    seed_symbols()
