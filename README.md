# AlgoTrading

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
python get.py calendar
python get.py news
python get.py timeframe
python get.py structure
python get.py position
python get.py swings
python get.py decision
```

## CLEAR CACHE

```bash
python get.py cache
```