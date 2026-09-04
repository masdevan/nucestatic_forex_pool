from zoneinfo import ZoneInfo
from datetime import datetime
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from app.api.routes.ohlc import router as ohlc_router

from app.api.models.configs.mt5_config import init_mt5, shutdown_mt5, get_terminal_info

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

@app.get("/api/health")
async def health_check():
    terminal = get_terminal_info()
    return {
        "status": "healthy",
        "mt5_connected": terminal is not None
    }

@app.on_event("shutdown")
async def shutdown_event():
    shutdown_mt5()