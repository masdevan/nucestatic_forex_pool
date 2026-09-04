import os
import importlib
import pymysql
from pathlib import Path
from sqlalchemy import text
from app.databases.config import engine, Base

MIGRATIONS_DIR = Path(__file__).parent
TABLE_NAME = "alembic_version"

TABLES = [
    "ohlc_m1",
    "ohlc_m5", 
    "ohlc_m15",
    "ohlc_h1",
]

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

def migrate_fresh():
    print("Running fresh migration...")
    print("Dropping all tables...")
    
    with engine.connect() as conn:
        for table in TABLES:
            conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
        conn.execute(text(f"DROP TABLE IF EXISTS {TABLE_NAME}"))
        conn.commit()
    
    print("All tables dropped.")
    
    run_migrations()
    
    print("Fresh migration complete.")
