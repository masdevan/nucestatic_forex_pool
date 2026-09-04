import os
from pathlib import Path
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.routes.ohlc import router as ohlc_router
from app.api.models.configs.mt5_config import init_mt5, shutdown_mt5, get_terminal_info, get_all_symbols

load_dotenv()

PORT = int(os.getenv("PORT", "8765"))

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

@app.get("/api/symbols")
async def symbols():
    return {"symbols": get_all_symbols()}

app.mount("/", StaticFiles(directory=Path(__file__).parent / "web", html=True), name="web")

@app.on_event("shutdown")
async def shutdown_event():
    shutdown_mt5()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=True
    )
