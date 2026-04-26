from fastapi import APIRouter, HTTPException
from app.api.configs.mt5_config import init_mt5, shutdown_mt5, get_symbols
from app.api.models.ohlc_model import SymbolsResponse

router = APIRouter()

@router.get("", response_model=SymbolsResponse)
async def get_available_symbols():
    if not init_mt5():
        raise HTTPException(status_code=500, detail="MT5 initialize failed")
    symbols = get_symbols()
    shutdown_mt5()
    if symbols is None:
        raise HTTPException(status_code=500, detail="Failed to retrieve symbols")
    return SymbolsResponse(symbols=[s.name for s in symbols], total=len(symbols))