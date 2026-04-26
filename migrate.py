import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.databases.migrations.manager import run_migrations, migrate_fresh

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python migrate migrate")
        print("       python migrate migrate:fresh")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "migrate":
        run_migrations()
    elif command == "migrate:fresh":
        confirm = input("This will drop all tables. Continue? (yes/no): ")
        if confirm.lower() == "yes":
            migrate_fresh()
        else:
            print("Cancelled.")
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)