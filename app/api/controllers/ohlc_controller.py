from datetime import datetime, time
from typing import List, Dict, Any
import MetaTrader5 as mt5
from app.api.configs.mt5_config import TIMEFRAME_MAP, init_mt5, shutdown_mt5, symbol_exists, get_rates_range, get_rates_from
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

def get_ohlc_today(pair: str, timeframe: str) -> OHLCResponse:
    if not init_mt5():
        raise Exception("MT5 initialize failed")
    
    if timeframe not in TIMEFRAME_MAP:
        shutdown_mt5()
        raise Exception("Invalid timeframe")
    
    if not symbol_exists(pair):
        shutdown_mt5()
        raise Exception("Symbol not found")
    
    today = datetime.now().date()
    start_dt = datetime.combine(today, time(0, 0, 0))
    end_dt = datetime.combine(today, time(23, 59, 59))
    start_ts = int(start_dt.timestamp())
    end_ts = int(end_dt.timestamp())
    
    tf = TIMEFRAME_MAP[timeframe]
    rates = get_rates_range(pair, tf, start_ts, end_ts)
    
    shutdown_mt5()
    
    if rates is None or len(rates) == 0:
        return OHLCResponse(
            pair=pair,
            timeframe=timeframe,
            start_date=today.strftime("%d%m%Y"),
            end_date=today.strftime("%d%m%Y"),
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
        start_date=today.strftime("%d%m%Y"),
        end_date=today.strftime("%d%m%Y"),
        data=data,
        total_records=len(data)
    )

def get_ohlc_all(pair: str) -> Dict[str, Any]:
    if not init_mt5():
        raise Exception("MT5 initialize failed")
    
    if not symbol_exists(pair):
        shutdown_mt5()
        raise Exception("Symbol not found")
    
    result = {}
    
    timeframe_configs = {
        "m1": 15,
        "m5": 15,
        "m15": 15,
        "m30": 15,
        "h1": 15,
    }
    
    for tf_name, count in timeframe_configs.items():
        tf = TIMEFRAME_MAP.get(tf_name)
        if tf is None:
            continue
        
        rates = mt5.copy_rates_from_pos(pair, tf, 0, count)
        
        if rates is None or len(rates) == 0:
            result[tf_name] = {
                "data": [],
                "total": 0
            }
        else:
            data = []
            for rate in rates:
                data.append({
                    "time": int(rate[0]),
                    "time_str": datetime.fromtimestamp(rate[0]).strftime("%Y-%m-%d %H:%M:%S"),
                    "open": float(rate[1]),
                    "high": float(rate[2]),
                    "low": float(rate[3]),
                    "close": float(rate[4]),
                })
            result[tf_name] = {
                "data": data,
                "total": len(data)
            }
    
    tick = mt5.symbol_info_tick(pair)
    result["current"] = {
        "bid": float(tick.bid),
        "ask": float(tick.ask),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    shutdown_mt5()
    return result