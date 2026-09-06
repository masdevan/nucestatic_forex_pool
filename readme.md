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

`migrate:fresh` akan menampilkan menu pemilihan kategori:
```
Select categories to seed (comma-separated):
  1. Forex Major       (7 symbols)
  2. Forex Cross       (21 symbols)
  3. Forex Exotic      (139 symbols)
  4. Crypto            (36 symbols)
  5. Indices           (15 symbols)
  6. Metals            (10 symbols)
  7. Commodities       (9 symbols)
  8. Stocks            (95 symbols)
  9. All

Choice: 1,4
```

## Seeding

```bash
python -m app.databases.seeders.symbol_seeder
python -m app.databases.seeders.symbol_range_seeder
python -m app.databases.seeders.ohlc_seeder
```

### OHLC Seeder Modes
- Single timeframe
- Single symbol, all timeframes
- Unseeded (skip yang sudah ada)
- Fresh (hapus data lama, seed ulang)
- Range (seed per range waktu)
