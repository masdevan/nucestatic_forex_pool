forex_pool
├── .env
├── .env.example
├── .gitignore
├── endpoints.md
├── main.py
├── migrate.py
├── readme.md
├── requirements.txt
├── rules.md
├── app
│   ├── main.py
│   ├── api
│   │   ├── __init__.py
│   │   ├── controllers
│   │   │   └── ohlc_controller.py
│   │   ├── models
│   │   │   ├── configs
│   │   │   │   └── mt5_config.py
│   │   │   └── ohlc_model.py
│   │   └── routes
│   │       └── ohlc.py
│   └── databases
│       ├── base.py
│       ├── config.py
│       ├── migrations
│       │   ├── manager.py
│       │   ├── version_20260329_ohlc_h1.py
│       │   ├── version_20260329_ohlc_m1.py
│       │   ├── version_20260329_ohlc_m15.py
│       │   └── version_20260329_ohlc_m5.py
│       └── models
