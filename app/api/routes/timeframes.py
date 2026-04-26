from fastapi import APIRouter
from app.api.configs.mt5_config import TIMEFRAME_MAP
from app.api.models.ohlc_model import TimeframesResponse

router = APIRouter()

@router.get("", response_model=TimeframesResponse)
async def get_available_timeframes():
    return TimeframesResponse(timeframes=list(TIMEFRAME_MAP.keys()))