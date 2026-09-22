forex_pool
├── .dockerignore
├── .env
├── .env.example
├── .gitignore
├── .vscode
│   ├── extensions.json
│   ├── launch.json
│   ├── settings.json
│   └── spellright.dict
├── CODE_OF_CONDUCT
├── Dockerfile
├── docker-compose.yml
├── endpoints.md
├── LICENSE
├── main.py
├── migrate.py
├── readme.md
├── requirements.txt
├── rules.md
├── structure.md
├── update.sh
├── app
│   ├── api
│   │   ├── controllers
│   │   │   └── ohlc_controller.py
│   │   ├── models
│   │   │   ├── configs
│   │   │   │   └── mt5_config.py
│   │   │   └── ohlc_model.py
│   └── databases
│       ├── base.py
│       ├── config.py
│       ├── migrations
│       │   ├── manager.py
│       │   ├── version_20260904_ohlc_dynamic.py
│       │   ├── version_20260904_symbol_ranges.py
│       │   ├── version_20260904_symbols.py
│       │   └── version_20260912_ohlc_page_anchor.py
│       ├── models
│       │   └── symbol_model.py
│       └── seeders
│           ├── anchor_seeder.py
│           ├── categories.py
│           ├── ohlc_seeder.py
│           ├── symbol_range_seeder.py
│           └── symbol_seeder.py
├── public
│   ├── favicon
│   │   ├── apple-touch-icon.png
│   │   ├── favicon-96x96.png
│   │   ├── favicon.ico
│   │   ├── favicon.svg
│   │   ├── site.webmanifest
│   │   ├── web-app-manifest-192x192.png
│   │   └── web-app-manifest-512x512.png
│   ├── logo.png
│   └── seamless_pattern.png
└── web
    ├── css
    │   └── styles.css
    ├── javascript
    │   ├── centrifugo.js
    │   ├── script.js
    │   └── symbol.js
    ├── index.html
    └── symbol.html
