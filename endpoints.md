# API ENDPOINTS

## Health
- GET /api/health
  - Returns: { status }

## Symbols
- GET /api/symbols?search={query}&limit=50&page=1
  - search: optional, filter symbol name (LIKE)
  - limit: default 50, max 1000
  - page: default 1
  - Returns: { symbols: [{ server, name }], total, pagination: { page, limit, total, total_pages, has_next, has_prev } }

- GET /api/symbols/{symbol}/range
  - Reads from the symbol_ranges table
  - Returns: { symbol, ranges: [{ timeframe, first, last, count }] }

## OHLC
- GET /api/ohlc/{symbol}?timeframe=m1&start_date=2024-01-01&end_date=2024-12-31&limit=50&cursor={ts}&before={ts}
  - symbol: required
  - timeframe: default m1 (m1, m5, m15, m30, h1, h4, d1, w1, mn1)
  - start_date: optional (format YYYY-MM-DD or YYYY-MM-DD HH:MM)
  - end_date: optional (format YYYY-MM-DD or YYYY-MM-DD HH:MM; date-only values become 23:59)
  - limit: default 50, max 1000
  - page: optional (OFFSET-based paging, still supported for direct access)
  - cursor: optional (unix timestamp in seconds of the last loaded row; FORWARD/ASC paging, faster than page)
  - before: optional (unix timestamp in seconds; BACKWARD/DESC paging - fetch rows with time < before, still returned ASC; use it to load older data or to start from the latest data). If both before and cursor are sent, before takes precedence
  - Queries a dynamic table: ohlc_{symbol}_{timeframe}
  - Returns: { symbol, timeframe, data: [{ symbol, open, high, low, close, time }], has_next, next_cursor }
    - has_next: false when there is no more data (the last batch contains fewer than limit+1 rows)
    - next_cursor: forward mode = timestamp of the last (newest) row sent; backward mode (before) = timestamp of the first (oldest) row sent; null when data is empty

## Centrifugo
- GET /api/centrifugo/token
  - Generates a JWT token for Centrifugo WebSocket
  - Returns: { token, ws_url }

## Pages
- GET / — Dashboard
- GET /{name}/{server} — Symbol detail page
