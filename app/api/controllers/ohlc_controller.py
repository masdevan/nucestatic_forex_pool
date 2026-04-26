from datetime import datetime, time
from typing import List, Dict, Any
import MetaTrader5 as mt5
from app.api.models.configs.mt5_config import TIMEFRAME_MAP, init_mt5, shutdown_mt5, symbol_exists, get_rates_range
from app.api.models.ohlc_model import OHLCData, OHLCResponse

def parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%d%m%Y")

def get_ohlc_data(pair: str, timeframe: str, start_date: str, end_date: str) -> OHLCResponse:
    if not init_mt5():
        raise Exception("MT5 initialize failed")
    
    if timeframe not in TIMEFRAME_MAP:
        shutdown_mt5()
        raise Exception("Invalid timeframe")
    
    if not symbol_exists(pair):
        shutdown_mt5()
        raise Exception("Symbol not found")
    
    start_dt = parse_date(start_date)
    end_dt = parse_date(end_date)
    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())
    
    tf = TIMEFRAME_MAP[timeframe]
    rates = get_rates_range(pair, tf, start_ts, end_ts)
    
    shutdown_mt5()
    
    if rates is None or len(rates) == 0:
        return OHLCResponse(
            pair=pair,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            data=[],
            total_records=0
        )
    
    data = []
    for rate in rates:
        data.append(OHLCData(
            time=int(rate[0]),
            time_str=datetime.fromtimestamp(rate[0]).strftime("%Y-%m-%d %H:%M:%S"),
            open=float(rate[1]),
            high=float(rate[2]),
            low=float(rate[3]),
            close=float(rate[4]),
            tick_volume=int(rate[5]),
            spread=int(rate[6]),
            real_volume=int(rate[7])
        ))
    
    return OHLCResponse(
        pair=pair,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        data=data,
        total_records=len(data)
    )