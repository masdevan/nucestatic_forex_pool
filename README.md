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

## Jobs

```bash
python get.py timeframe
python get.py calendar
python get.py news
```

## CLEAR CACHE

```bash
python get.py cache
```