# API ENDPOINTS

## Health
- GET /api/health
  - Returns: { status, mt5_connected }

## Symbols
- GET /api/symbols
  - Returns: { symbols: [{ server, name }] }

- GET /api/symbols/{symbol}/range
  - Returns data dari tabel symbol_ranges
  - Returns: { symbol, ranges: [{ timeframe, first, last, count }] }

- GET /api/symbols/{symbol}/date-range?timeframe=m1&start_date=2024-01-01&end_date=2024-12-31&limit=50
  - symbol: required
  - timeframe: default m1
  - start_date: optional (format YYYY-MM-DD HH:MM)
  - end_date: optional (format YYYY-MM-DD HH:MM)
  - limit: default 50
  - Query ke tabel ohlc_{symbol}_{timeframe}
  - Returns: { symbol, timeframe, data: [{ symbol, open, high, low, close, time }], total }

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

## Centrifugo
- GET /api/centrifugo/token
  - Generate JWT token untuk Centrifugo WebSocket
  - Returns: { token, ws_url }

## Pages
- GET / — Dashboard
- GET /{name}/{server} — Symbol detail page
