# API ENDPOINTS

## Health
- GET /api/health
  - Returns: { status }

## Symbols
- GET /api/symbols?search={query}&limit=50&page=1
  - search: optional, filter nama symbol (LIKE)
  - limit: default 50, max 1000
  - page: default 1
  - Returns: { symbols: [{ server, name }], total, pagination: { page, limit, total, total_pages, has_next, has_prev } }

- GET /api/symbols/{symbol}/range
  - Returns data dari tabel symbol_ranges
  - Returns: { symbol, ranges: [{ timeframe, first, last, count }] }

## OHLC
- GET /api/ohlc/{symbol}?timeframe=m1&start_date=2024-01-01&end_date=2024-12-31&limit=50&cursor={ts}
  - symbol: required
  - timeframe: default m1 (m1, m5, m15, m30, h1, h4, d1, w1, mn1)
  - start_date: optional (format YYYY-MM-DD atau YYYY-MM-DD HH:MM)
  - end_date: optional (format YYYY-MM-DD atau YYYY-MM-DD HH:MM, bertipe tanggal -> otomatis 23:59)
  - limit: default 50, max 1000
  - page: opsional (halaman berbasis OFFSET, tetap didukung untuk akses langsung)
  - cursor: opsional (unix ts detik baris terakhir yang sudah dimuat; untuk paging berantai, lebih cepat daripada page)
  - Query ke tabel dinamis: ohlc_{symbol}_{timeframe}
  - Returns: { symbol, timeframe, data: [{ symbol, open, high, low, close, time }], has_next, next_cursor }
    - has_next: false saat tidak ada data lagi (data terakhir berisi kurang dari limit+1 baris)
    - next_cursor: unix ts detik baris terakhir yang dikirim, untuk request berikutnya; null saat data kosong

## Centrifugo
- GET /api/centrifugo/token
  - Generate JWT token untuk Centrifugo WebSocket
  - Returns: { token, ws_url }

## Pages
- GET / — Dashboard
- GET /{name}/{server} — Symbol detail page
