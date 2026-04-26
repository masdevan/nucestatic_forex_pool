from zoneinfo import ZoneInfo
from datetime import datetime
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from app.api.routes.ohlc import router as ohlc_router
from app.api.routes.calendar import router as calendar_router
from app.api.routes.news import router as news_router

from app.api.models.configs.mt5_config import init_mt5, shutdown_mt5, get_terminal_info

JAKARTA_TZ = ZoneInfo("Asia/Jakarta")

if not init_mt5():
    print("MT5 initialization failed")
else:
    print("MT5 initialized successfully")

app = FastAPI(
    title="FOREXPOOL",
    description="API for algorithmic trading with MetaTrader 5",
    version="1.0.0"
)

app.include_router(ohlc_router, prefix="/api/ohlc", tags=["OHLC"])
app.include_router(calendar_router, prefix="/api", tags=["Calendar"])
app.include_router(news_router, prefix="/api", tags=["News"])

@app.get("/api/health")
async def health_check():
    terminal = get_terminal_info()
    return {
        "status": "healthy",
        "mt5_connected": terminal is not None
    }

@app.get("/api/time/now")
async def time_now():
    now = datetime.now(JAKARTA_TZ)
    hour = now.hour

    if 6 <= hour < 14:
        session_id = 1
        session = 'Asia'
    elif 14 <= hour < 19:
        session_id = 2
        session = 'London'
    else:
        session_id = 3
        session = 'New York'

    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "session": session,
        "session_id": session_id
    }

@app.on_event("shutdown")
async def shutdown_event():
    shutdown_mt5()