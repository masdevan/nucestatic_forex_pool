## Requirements

```bash
pip install -r requirements.txt
```

## Running the Application

```bash
python main.py
```

## Database Migrations

Database will be created automatically if not exists.

```bash
python migrate.py migrate
python migrate.py migrate:fresh
```

## Seeding Symbols

Populate the `symbols` table with all symbols from the connected MT5 terminal (each stored with its account server):

```bash
python -m app.databases.seeders.symbol_seeder
```

The seeder reads the account server from MT5 (e.g. `Exness-MT5Trial6`) and inserts each symbol paired with that server. The same symbol name can exist on different servers, but a `(server, name)` pair is unique.
