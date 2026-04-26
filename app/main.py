from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from app.api.routes.ohlc import router as ohlc_router
from app.api.routes.symbols import router as symbols_router
from app.api.routes.timeframes import router as timeframes_router
from app.api.routes.positions import router as positions_router
from app.api.routes.account import router as account_router
from app.api.routes.calendar import router as calendar_router
from app.api.routes.news import router as news_router
from app.api.routes.market_structure import router as market_structure_router
from app.api.routes.execution import router as execution_router
from app.api.routes.swings import router as swings_router

from app.api.configs.mt5_config import init_mt5, shutdown_mt5, get_terminal_info

if not init_mt5():
    print("MT5 initialization failed")
else:
    print("MT5 initialized successfully")

app = FastAPI(
    title="AlgoTrading API",
    description="API for algorithmic trading with MetaTrader 5",
    version="1.0.0"
)

app.include_router(ohlc_router, prefix="/api/ohlc", tags=["OHLC"])
app.include_router(symbols_router, prefix="/api/symbols", tags=["Symbols"])
app.include_router(timeframes_router, prefix="/api/timeframes", tags=["Timeframes"])
app.include_router(positions_router, prefix="/api/positions", tags=["Positions"])
app.include_router(account_router, prefix="/api/account", tags=["Account"])
app.include_router(calendar_router, prefix="/api", tags=["Calendar"])
app.include_router(news_router, prefix="/api", tags=["News"])
app.include_router(market_structure_router, prefix="/api/market_structure", tags=["Market Structure"])
app.include_router(execution_router, prefix="/api/execution", tags=["Execution"])
app.include_router(swings_router, prefix="/api/swings", tags=["Swings"])


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
resources_path = os.path.join(BASE_DIR, "app", "resources")
app.mount("/resources", StaticFiles(directory=resources_path), name="resources")

def get_view_path(filename: str):
    return os.path.join(resources_path, "views", filename)

@app.get("/")
async def root():
    return FileResponse(get_view_path("index.html"))

@app.get("/dashboard")
async def dashboard():
    return FileResponse(get_view_path("index.html"))

@app.get("/charts")
async def charts_page():
    return FileResponse(get_view_path("charts.html"))

@app.get("/api/config")
async def get_config():
    trade_pair = os.getenv("TRADE_PAIR", "USDJPYm")
    symbols = [s.strip() for s in trade_pair.split(",") if s.strip()]
    return {"trade_pair": trade_pair, "symbols": symbols}

@app.get("/account")
async def account_page():
    return FileResponse(get_view_path("account.html"))

@app.get("/positions")
async def positions_page():
    return FileResponse(get_view_path("orders.html"))

@app.get("/calendar")
async def calendar_page():
    return FileResponse(get_view_path("calendar.html"))

@app.get("/news")
async def news_page():
    return FileResponse(get_view_path("news.html"))

@app.get("/ohlc")
async def ohlc_page():
    return FileResponse(get_view_path("ohlc.html"))

@app.get("/market_structure")
async def market_structure_page():
    return FileResponse(get_view_path("market_structure.html"))

@app.get("/swings")
async def swings_page():
    return FileResponse(get_view_path("swings.html"))

@app.get("/performance")
async def performance_page():
    return FileResponse(get_view_path("performance.html"))

@app.get("/health")
async def health_check():
    terminal = get_terminal_info()
    return {
        "status": "healthy",
        "mt5_connected": terminal is not None
    }

@app.on_event("shutdown")
async def shutdown_event():
    shutdown_mt5()