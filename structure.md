forex_pool
├── .env
├── .env.example
├── .gitignore
├── .vscode
│   ├── extensions.json
│   ├── launch.json
│   ├── settings.json
│   ├── spellright.dict
│   └── tasks.json
├── endpoints.md
├── main.py
├── migrate.py
├── readme.md
├── requirements.txt
├── rules.md
├── structure.md
├── app
│   ├── api
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
│       │   ├── version_20260329_ohlc_m5.py
│       │   ├── version_20260904_symbols.py
│       │   └── version_20260904_symbol_ranges.py
│       ├── models
│       │   └── symbol_model.py
│       └── seeders
│           ├── symbol_range_seeder.py
│           └── symbol_seeder.py
└── web
    ├── css
    │   └── styles.css
    ├── javascript
    │   └── script.js
    ├── index.html
    └── symbol.html
