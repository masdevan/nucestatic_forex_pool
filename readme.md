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

## Seeding 

```bash
python -m app.databases.seeders.symbol_seeder
python -m app.databases.seeders.symbol_range_seeder
```