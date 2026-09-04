import MetaTrader5 as mt5
from datetime import datetime, time

TIMEFRAME_MAP = {
    "m1": mt5.TIMEFRAME_M1,
    "m5": mt5.TIMEFRAME_M5,
    "m15": mt5.TIMEFRAME_M15,
    "m30": mt5.TIMEFRAME_M30,
    "h1": mt5.TIMEFRAME_H1,
    "h4": mt5.TIMEFRAME_H4,
    "d1": mt5.TIMEFRAME_D1,
    "w1": mt5.TIMEFRAME_W1,
    "mn1": mt5.TIMEFRAME_MN1,
}

def init_mt5():
    if not mt5.initialize():
        return False
    return True

def shutdown_mt5():
    mt5.shutdown()

def get_terminal_info():
    return mt5.terminal_info()

def symbol_exists(symbol: str):
    return mt5.symbol_info(symbol) is not None

def get_rates_range(symbol: str, timeframe, start_ts: int, end_ts: int):
    return mt5.copy_rates_range(symbol, timeframe, start_ts, end_ts)

def symbol_info_tick(symbol: str):
    return mt5.symbol_info_tick(symbol)

def _count_available(symbol: str, timeframe) -> int:
    high = 1
    while mt5.copy_rates_from_pos(symbol, timeframe, high, 1) is not None:
        high *= 2
    low = high // 2
    while low < high:
        mid = (low + high + 1) // 2
        if mt5.copy_rates_from_pos(symbol, timeframe, mid - 1, 1) is not None:
            low = mid
        else:
            high = mid - 1
    return low

def get_mt5_range(symbol: str, timeframe) -> dict:
    total = _count_available(symbol, timeframe)
    if total == 0:
        return {"first": None, "last": None, "count": 0}
    first = mt5.copy_rates_from_pos(symbol, timeframe, total - 1, 1)
    last = mt5.copy_rates_from_pos(symbol, timeframe, 0, 1)
    return {
        "first": datetime.fromtimestamp(int(first[0][0])).strftime("%Y-%m-%d %H:%M:%S") if first is not None else None,
        "last": datetime.fromtimestamp(int(last[0][0])).strftime("%Y-%m-%d %H:%M:%S") if last is not None else None,
        "count": total,
    }