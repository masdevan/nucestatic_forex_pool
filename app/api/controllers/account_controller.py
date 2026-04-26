from app.api.configs.mt5_config import init_mt5, shutdown_mt5, get_account_info, get_positions
from typing import Dict, Any

def get_account() -> Dict[str, Any]:
    if not init_mt5():
        raise Exception("MT5 initialize failed")
    
    info = get_account_info()
    positions = get_positions()
    shutdown_mt5()
    
    if info is None:
        raise Exception("Failed to get account info")
    
    positions_count = len(positions) if positions else 0
    
    account_data = {
        "login": info.login,
        "trade_mode": info.trade_mode,
        "leverage": info.leverage,
        "balance": info.balance,
        "credit": info.credit,
        "profit": info.profit,
        "equity": info.equity,
        "margin": info.margin,
        "margin_free": info.margin_free,
        "margin_level": info.margin_level,
        "server": info.server,
        "currency": info.currency,
        "company": info.company,
        "name": info.name,
        "positions": positions_count
    }
    
    return account_data