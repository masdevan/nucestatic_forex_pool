import os
import importlib
import pymysql
from pathlib import Path
from sqlalchemy import text
from app.databases.config import engine, Base

MIGRATIONS_DIR = Path(__file__).parent
TABLE_NAME = "alembic_version"

def ensure_database():
    from app.databases.config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=int(MYSQL_PORT),
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        with conn.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE}")
        conn.close()
        print(f"Database '{MYSQL_DATABASE}' ensured.")
    except Exception as e:
        print(f"Error creating database: {e}")
        raise

def create_version_table():
    ensure_database()
    with engine.connect() as conn:
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                version VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.commit()

def get_applied_versions():
    create_version_table()
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT version FROM {TABLE_NAME}"))
        return [row[0] for row in result.fetchall()]

def run_migrations():
    print("Running migrations...")
    ensure_database()
    create_version_table()

    applied_versions = get_applied_versions()
    print(f"Applied versions: {len(applied_versions)}")

    migration_files = sorted([
        f for f in os.listdir(MIGRATIONS_DIR)
        if f.endswith(".py") and f.startswith("version_")
    ])

    if not migration_files:
        print("No migration files found.")
        return

    applied_count = 0

    for migration_file in migration_files:
        version = migration_file.replace("version_", "").replace(".py", "")

        if version in applied_versions:
            continue

        print(f"Applying migration: {version}")

        module_name = f"app.databases.migrations.{migration_file[:-3]}"
        module = importlib.import_module(module_name)

        if hasattr(module, "upgrade"):
            with engine.begin() as conn:
                module.upgrade(conn)

        with engine.connect() as conn:
            conn.execute(text(f"INSERT INTO {TABLE_NAME} (version) VALUES (:version)"), {"version": version})
            conn.commit()

        print(f"Migration {version} applied successfully")
        applied_count += 1

    if applied_count == 0:
        print("Nothing to migrate.")
    else:
        print(f"Migration complete. Applied {applied_count} migration(s).")

def drop_all_tables():
    with engine.connect() as conn:
        result = conn.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result.fetchall()]
        for table in tables:
            conn.execute(text(f"DROP TABLE IF EXISTS `{table}`"))
        conn.commit()
    print(f"Dropped {len(tables)} tables")

def prompt_category_selection():
    from app.databases.seeders.categories import CATEGORIES

    names = list(CATEGORIES.keys())
    print("\nSelect categories to seed (comma-separated):")
    for i, name in enumerate(names, 1):
        count = len(CATEGORIES[name])
        print(f"  {i}. {name:<20} ({count} symbols)")
    print(f"  {len(names) + 1}. All")

    raw = input("\nChoice: ").strip()
    if not raw:
        print("No selection. Aborting.")
        return None

    choices = [c.strip() for c in raw.split(",")]
    all_nums = list(range(1, len(names) + 1))

    if str(len(names) + 1) in choices:
        selected = []
        for name in names:
            selected.extend(CATEGORIES[name])
        print(f"All categories selected ({len(selected)} symbols)")
        return selected

    selected = []
    selected_names = []
    for c in choices:
        if c.isdigit():
            idx = int(c) - 1
            if 0 <= idx < len(names):
                selected.extend(CATEGORIES[names[idx]])
                selected_names.append(names[idx])

    if not selected:
        print("Invalid selection. Aborting.")
        return None

    print(f"Selected {len(selected)} symbols ({', '.join(selected_names)})")
    return selected


def seed_symbols_by_category(symbols):
    from sqlalchemy import text as sql_text
    with engine.begin() as conn:
        for name in symbols:
            conn.execute(sql_text(
                "INSERT INTO symbols (server, name) VALUES (:server, :name) "
                "ON DUPLICATE KEY UPDATE server = VALUES(server)"
            ), {"server": "", "name": name})
    print(f"Seeded {len(symbols)} symbols.")


def migrate_fresh():
    print("Running fresh migration...")
    print("Dropping all tables...")

    drop_all_tables()

    print("All tables dropped.")

    create_version_table()

    print("Creating symbols table...")
    module = importlib.import_module("app.databases.migrations.version_20260904_symbols")
    with engine.begin() as conn:
        module.upgrade(conn)
    with engine.connect() as conn:
        conn.execute(text(f"INSERT INTO {TABLE_NAME} (version) VALUES (:version)"), {"version": "20260904_symbols"})
        conn.commit()

    selected = prompt_category_selection()
    if not selected:
        return

    init_mt5 = False
    try:
        import MetaTrader5 as mt5
        if mt5.initialize():
            init_mt5 = True
            account = mt5.account_info()
            server = account.server if account else ""
            mt5.shutdown()
        else:
            server = ""
    except Exception:
        server = ""

    from sqlalchemy import text as sql_text
    with engine.begin() as conn:
        for name in selected:
            conn.execute(sql_text(
                "INSERT INTO symbols (server, name) VALUES (:server, :name) "
                "ON DUPLICATE KEY UPDATE server = VALUES(server)"
            ), {"server": server, "name": name})
    print(f"Seeded {len(selected)} symbols.")

    run_migrations()

    print("Fresh migration complete.")
