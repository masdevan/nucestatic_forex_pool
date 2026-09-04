import MetaTrader5 as mt5
from sqlalchemy import text
from app.databases.config import engine

def seed_symbols():
    if not mt5.initialize():
        print("MT5 initialize failed")
        return
    symbols = [s.name for s in mt5.symbols_get()] if mt5.symbols_get() else []
    mt5.shutdown()

    with engine.begin() as conn:
        for name in symbols:
            conn.execute(
                text("INSERT IGNORE INTO symbols (name) VALUES (:name)"),
                {"name": name},
            )
    print(f"Seeded {len(symbols)} symbols")

if __name__ == "__main__":
    seed_symbols()
