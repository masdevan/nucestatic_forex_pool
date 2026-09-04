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

## Seeding Symbol Chart Ranges

Populate `symbol_ranges` with each symbol's oldest/newest chart bar per timeframe (read directly from the connected MT5 terminal):

```bash
python -m app.databases.seeders.symbol_range_seeder
```

To seed a single symbol (faster, for testing):

```bash
python -m app.databases.seeders.symbol_range_seeder BTCUSDm
```

Seeding all symbols scans MT5 history for each symbol × timeframe, so the full run takes a while.
