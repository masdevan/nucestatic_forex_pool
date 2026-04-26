# OHLC ENDPOINTS
- GET /api/ohlc?pair=XAUUSD&timeframe=m1&start_date=05122026&end_date=10122026
- GET /api/ohlc/today?pair=XAUUSD&timeframe=m1
- GET /api/ohlc/all?pair=XAUUSD
- GET /api/ohlc/M1?symbol=BTCUSDm&page=1&limit=50
- GET /api/ohlc/M5?symbol=BTCUSDm&page=1&limit=50
- GET /api/ohlc/M15?symbol=BTCUSDm&page=1&limit=50
- GET /api/ohlc/H1?symbol=BTCUSDm&page=1&limit=50
- GET /api/ohlc/charts/M1?symbol=BTCUSDm
- GET /api/ohlc/charts/M5?symbol=BTCUSDm
- GET /api/ohlc/charts/M15?symbol=BTCUSDm
- GET /api/ohlc/charts/H1?symbol=BTCUSDm

# SWINGS ENDPOINTS
- GET /api/swings/charts/M1?symbol=BTCUSDm
- GET /api/swings/charts/M5?symbol=BTCUSDm
- GET /api/swings/charts/M15?symbol=BTCUSDm
- GET /api/swings/charts/H1?symbol=BTCUSDm
- GET /api/swings/M1?symbol=BTCUSDm&page=1&limit=50
- GET /api/swings/M5?symbol=BTCUSDm&page=1&limit=50
- GET /api/swings/M15?symbol=BTCUSDm&page=1&limit=50
- GET /api/swings/H1?symbol=BTCUSDm&page=1&limit=50
- GET /api/swings/charts/M1?symbol=USDJPYm

# MARKET STRUCTURE ENDPOINTS
- GET /api/market_structure/charts/M1?symbol=BTCUSDm
- GET /api/market_structure/charts/M5?symbol=BTCUSDm
- GET /api/market_structure/charts/M15?symbol=BTCUSDm
- GET /api/market_structure/charts/H1?symbol=BTCUSDm
- GET /api/market_structure/M1?symbol=BTCUSDm&page=1&limit=50
- GET /api/market_structure/M5?symbol=BTCUSDm&page=1&limit=50
- GET /api/market_structure/M15?symbol=BTCUSDm&page=1&limit=50
- GET /api/market_structure/H1?symbol=BTCUSDm&page=1&limit=50

# EXECUTION ENDPOINTS
- GET /api/execution/time/now

- GET /api/execution/total_loss_today?symbol=USDJPYm
- GET /api/execution/spread?symbol=USDJPYm
- GET /api/execution/position_total?symbol=USDJPYm
- GET /api/execution/risk_reward?symbol=USDJPYm

- GET /api/execution/news?symbol=USDJPYm
- GET /api/execution/calendar?symbol=USDJPYm

- GET /api/execution/market_structure?symbol=USDJPYm
- GET /api/execution/swing?symbol=USDJPYm
- GET /api/execution/accuracy?symbol=USDJPYm&type=buy
- GET /api/execution/candle_speed?symbol=USDJPYm

# POSITION ENDPOINTS
- GET /api/positions
- GET /api/positions/chart/history?symbol=USDJPYm
- GET /api/positions/db?page=1&per_page=20&is_running=1
- GET /api/positions/db/today?page=1&per_page=20
- GET /api/positions/history?from_date=24032026&to_date=25032026
- GET /api/positions/history/today
- GET /api/positions/performance
- GET /api/positions/chart/history?symbol=USDJPYm
- POST /api/positions/open/market
  ```json
  {
    "symbol": "XAUUSD",
    "volume": 0.1,
    "type": "buy",
    "sl": 2040.0,
    "tp": 2060.0
  }
  ```
- POST /api/positions/open/limit
  ```json
  {
    "symbol": "XAUUSD",
    "volume": 0.1,
    "type": "buy",
    "price": 2050.0,
    "sl": 2040.0,
    "tp": 2060.0
  }
  ```
- POST /api/positions/close
  ```json
  {
    "ticket": 123456
  }
  ```
- POST /api/positions/close_all
- POST /api/positions/modify
  ```json
  {
    "ticket": 123456,
    "sl": 2045.0,
    "tp": 2055.0,
    "volume": 0.2
  }
  ```

# BASE INFO ENDPOINTS
- GET /api/symbols
- GET /api/timeframes
- GET /api/account/summary
- GET /api/account
- GET /health

# CALENDAR ENDPOINTS
- GET /api/calendar
- GET /api/calendar?page=1&limit=50&currency=EUR&impact=high&start_date=2026-03-01&end_date=2026-03-31
- GET /api/calendar/today

# NEWS ENDPOINTS
- GET /api/news
- GET /api/news?page=1&limit=50&news_date=2026-03-26
- GET /api/news/today
