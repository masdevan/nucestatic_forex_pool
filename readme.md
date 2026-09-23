<img src="https://i.imgur.com/jOh9vu6.png" alt="Berruang Preview" width="100%">

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

## MQL5 Ingest Service (Dynamic Mode)

Runs as an MT5 service, no chart needed.

1. Copy `forex_pool_ingest.mq5` to `MQL5\Services\` (File > Open Data Folder > MQL5 > Services)
2. Compile it in MetaEditor (F7)
3. Navigator > Services > right-click > Add Service (once; it auto-starts with the terminal afterwards)
4. Allow the API URL in Tools > Options > Expert Advisors > Allow WebRequest for listed URL

- Edit `SYMBOL` at the top of the file (`BTCUSDm,XAUUSDm,...`), then recompile and restart the service instance to change symbols
- Inputs: `InpApiBase`, `InpServer` (empty = account server), `InpMinStartDate` (fallback when `/api/health` is unreachable), `InpPollMs`, `InpBatchSize`
- Every timeframe is backfilled from `MIN_START_DATE` (env, also served by `/api/health`), then only new or changed candles are posted to `POST /api/ohlc`
- Gaps inside the backfill window are closed automatically because every start re-sends the window (idempotent upsert)
- If the API is unreachable the service backs off up to 60 seconds and keeps retrying; symbols that are not available yet are retried every cycle
