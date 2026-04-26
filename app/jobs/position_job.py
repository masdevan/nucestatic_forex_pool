import sys
import time
from datetime import datetime
from app.databases.config import SessionLocal
from app.databases.models.positions_model import Positions
from app.api.configs.mt5_config import init_mt5, shutdown_mt5, get_positions

def get_order_type_string(order_type: int) -> str:
    import MetaTrader5 as mt5
    if order_type == mt5.ORDER_TYPE_BUY:
        return "buy"
    elif order_type == mt5.ORDER_TYPE_SELL:
        return "sell"
    elif order_type == mt5.ORDER_TYPE_BUY_LIMIT:
        return "buy_limit"
    elif order_type == mt5.ORDER_TYPE_SELL_LIMIT:
        return "sell_limit"
    return "unknown"

def sync_positions():
    db = SessionLocal()
    try:
        if not init_mt5():
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] MT5 init failed")
            return
        
        mt5_positions = get_positions()
        
        if mt5_positions is None:
            shutdown_mt5()
            return
        
        db_positions = db.query(Positions).filter(Positions.is_running == 1).all()
        db_tickets = {pos.ticket: pos for pos in db_positions}
        
        mt5_tickets = {pos.ticket: pos for pos in mt5_positions}
        
        for ticket, db_pos in db_tickets.items():
            if ticket not in mt5_tickets:
                db_pos.is_running = 0
                db_pos.closed_by = "tp_sl"
                db.commit()
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Position {ticket} closed (TP/SL)")
            else:
                mt5_pos = mt5_tickets[ticket]
                
                db_sl = float(db_pos.sl) if db_pos.sl else 0
                db_tp = float(db_pos.tp) if db_pos.tp else 0
                mt5_sl = float(mt5_pos.sl) if mt5_pos.sl else 0
                mt5_tp = float(mt5_pos.tp) if mt5_pos.tp else 0
                
                updated = False
                
                if round(db_sl, 5) != round(mt5_sl, 5):
                    db_pos.sl = mt5_pos.sl
                    updated = True
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Position {ticket} SL changed: {db_sl} -> {mt5_sl}")
                
                if round(db_tp, 5) != round(mt5_tp, 5):
                    db_pos.tp = mt5_pos.tp
                    updated = True
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Position {ticket} TP changed: {db_tp} -> {mt5_tp}")
                
                db_volume = float(db_pos.volume) if db_pos.volume else 0
                if round(db_volume, 2) != round(mt5_pos.volume, 2):
                    db_pos.volume = mt5_pos.volume
                    updated = True
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Position {ticket} volume changed: {db_volume} -> {mt5_pos.volume}")
                
                db_profit = float(db_pos.profit) if db_pos.profit else 0
                if round(db_profit, 2) != round(mt5_pos.profit, 2):
                    db_pos.profit = mt5_pos.profit
                    updated = True
                
                if updated:
                    db.commit()
        
        for ticket, mt5_pos in mt5_tickets.items():
            if ticket not in db_tickets:
                new_pos = Positions(
                    ticket=mt5_pos.ticket,
                    symbol=mt5_pos.symbol,
                    type=get_order_type_string(mt5_pos.type),
                    volume=mt5_pos.volume,
                    price=mt5_pos.price_open,
                    sl=mt5_pos.sl,
                    tp=mt5_pos.tp,
                    profit=mt5_pos.profit,
                    time=datetime.fromtimestamp(mt5_pos.time).strftime("%Y-%m-%d %H:%M:%S"),
                    is_running=1
                )
                db.add(new_pos)
                db.commit()
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] New position added: {ticket} {mt5_pos.symbol}")
        
        shutdown_mt5()
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Error: {e}")
    finally:
        db.close()

def run_job():
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Position monitor started")
    loop_count = 0
    
    while True:
        try:
            sync_positions()
            loop_count += 1
            
            if loop_count >= 200:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Cycle complete, clearing cache...")
                loop_count = 0
            
            time.sleep(0.5)
        except KeyboardInterrupt:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Position monitor stopped")
            break
        except Exception as e:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Critical error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_job()
