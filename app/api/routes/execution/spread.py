from fastapi import APIRouter, Query
import os
import MetaTrader5 as mt5
from app.api.configs.mt5_config import init_mt5

router = APIRouter()

LOT_SIZE = float(os.getenv("LOT_SIZE", "0.01"))


def get_pip_size(digits: int, point: float) -> float:
    if digits % 2 == 1:
        return point * 10
    return point


def get_usd_rate(currency: str) -> float:
    if currency == "USD":
        return 1.0

    all_symbols = [s.name for s in mt5.symbols_get()]

    for sym in all_symbols:
        if sym.startswith(currency + "USD"):
            tick = mt5.symbol_info_tick(sym)
            if tick:
                return tick.ask

    for sym in all_symbols:
        if sym.startswith("USD" + currency):
            tick = mt5.symbol_info_tick(sym)
            if tick:
                return 1.0 / tick.ask

    return 1.0


@router.get("/spread")
async def get_execution_spread(
    symbol: str = Query(..., description="Symbol to get spread information")
):
    if not init_mt5():
        return {"symbol": symbol, "spread_pips": 0, "price_dollars": 0, "volume": LOT_SIZE, "mt5_connected": False}

    symbol_info = mt5.symbol_info(symbol)
    if not symbol_info:
        return {"symbol": symbol, "spread_pips": 0, "price_dollars": 0, "volume": LOT_SIZE, "symbol_found": False}

    point = symbol_info.point
    spread_price = symbol_info.spread * point
    spread_pips = spread_price / get_pip_size(symbol_info.digits, point)

    spread_cost_raw = spread_price * symbol_info.trade_contract_size * LOT_SIZE
    usd_rate = get_usd_rate(symbol_info.currency_profit)
    spread_cost_usd = spread_cost_raw * usd_rate

    return {
        "symbol": symbol,
        "spread_pips": round(spread_pips, 2),
        "price_dollars": round(spread_cost_usd, 4),
        "volume": LOT_SIZE
    }