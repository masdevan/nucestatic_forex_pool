# OHLC ENDPOINTS
- GET /api/ohlc/{timeframe}?symbol=BTCUSDm&start_time=1700000000&end_time=1700100000&page=1&limit=50
  - symbol: required
  - timeframe: m1, m5, m15, m30, h1, h4, d1, w1, mn1
  - Query ke tabel dinamis: ohlc_{symbol}_{timeframe}
  - Returns: symbol, time, open, high, low, close

# BASE INFO ENDPOINTS
- GET /api/symbols
- GET /api/symbols/{symbol}/range
- GET /api/health
