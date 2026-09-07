# API ENDPOINTS

## Health
- GET /api/health
  - Returns: { status, mt5_connected }

## Symbols
- GET /api/symbols
  - Returns: { symbols: [{ server, name }] }

- GET /api/symbols/{symbol}/range
  - Returns: { symbol, ranges: [{ timeframe, first, last, count }] }

## OHLC
- GET /api/ohlc/{timeframe}?symbol=BTCUSDm&start_time=1700000000&end_time=1700100000&page=1&limit=50
  - symbol: required
  - timeframe: m1, m5, m15, m30, h1, h4, d1, w1, mn1
  - start_time: optional (Unix timestamp)
  - end_time: optional (Unix timestamp)
  - page: default 1
  - limit: default 50, max 100
  - Query ke tabel dinamis: ohlc_{symbol}_{timeframe}
  - Returns: { data: [{ symbol, time, open, high, low, close }], pagination: { page, limit, total, total_pages, has_next, has_prev } }

## Pages
- GET / — Dashboard
- GET /{name}/{server} — Symbol detail page
