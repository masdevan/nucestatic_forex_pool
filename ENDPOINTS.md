# OHLC ENDPOINTS
- GET /api/ohlc/{timeframe}?symbol=BTCUSDm&page=1&limit=50
- GET /api/ohlc?pair=XAUUSD&timeframe=m1&start_date=05122026&end_date=10122026

# CALENDAR ENDPOINTS
- GET /api/calendar
- GET /api/calendar?page=1&limit=50&currency=EUR&impact=high&start_date=2026-03-01&end_date=2026-03-31
- GET /api/calendar/today

# NEWS ENDPOINTS
- GET /api/news
- GET /api/news?page=1&limit=50&news_date=2026-03-26
- GET /api/news/today

# BASE INFO ENDPOINTS
- GET /api/symbols
- GET /api/timeframes
- GET /health