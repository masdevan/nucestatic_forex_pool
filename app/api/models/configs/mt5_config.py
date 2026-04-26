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

def get_account_info():
    return mt5.account_info()

def get_symbols():
    return mt5.symbols_get()

def symbol_exists(symbol: str):
    return mt5.symbol_info(symbol) is not None

def get_rates_range(symbol: str, timeframe, start_ts: int, end_ts: int):
    return mt5.copy_rates_range(symbol, timeframe, start_ts, end_ts)

def get_rates_from(symbol: str, timeframe, from_ts: int, count: int):
    return mt5.copy_rates_from(symbol, timeframe, from_ts, count)

def get_positions():
    return mt5.positions_get()

def symbol_info(symbol: str):
    return mt5.symbol_info(symbol)

def symbol_info_tick(symbol: str):
    return mt5.symbol_info_tick(symbol)

def order_send(request_dict):
    return mt5.order_send(request_dict)

def close_position(ticket: int):
    positions = mt5.positions_get()
    for pos in positions:
        if pos.ticket == ticket:
            symbol_info = mt5.symbol_info(pos.symbol)
            symbol_digits = symbol_info.digits
            order_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
            price = mt5.symbol_info_tick(pos.symbol).bid if pos.type == 0 else mt5.symbol_info_tick(pos.symbol).ask
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": order_type,
                "price": price,
                "deviation": 20,
                "magic": pos.magic,
                "comment": f"Close {ticket}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
                "position": ticket,
            }
            return mt5.order_send(request)
    return None

def close_all_positions():
    positions = mt5.positions_get()
    if positions is None or len(positions) == 0:
        return []
    
    closed = []
    for pos in positions:
        symbol_info = mt5.symbol_info(pos.symbol)
        symbol_digits = symbol_info.digits
        order_type = mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(pos.symbol).bid if pos.type == 0 else mt5.symbol_info_tick(pos.symbol).ask
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": order_type,
            "price": price,
            "deviation": 20,
            "magic": pos.magic,
            "comment": f"Close {pos.ticket}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
            "position": pos.ticket,
        }
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            closed.append(pos.ticket)
    return closed

def get_history_deals(from_date: int, to_date: int):
    return mt5.history_deals_get(from_date, to_date)

def get_history_orders(from_date: int, to_date: int):
    return mt5.history_orders_get(from_date, to_date)