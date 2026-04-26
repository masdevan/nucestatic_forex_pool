from datetime import datetime
from typing import List, Union, Optional
import MetaTrader5 as mt5
from app.api.configs.mt5_config import init_mt5, shutdown_mt5, get_positions, close_position, close_all_positions as mt5_close_all_positions, get_history_deals, get_history_orders
from app.databases.config import SessionLocal
from app.databases.models.positions_model import Positions
from app.api.models.position_model import (
    PositionInfo, PositionsResponse, PositionResponse, 
    OpenMarketRequest, OpenLimitRequest, ClosePositionRequest, 
    ModifyPositionRequest, ActionResponse, HistoryResponse, 
    HistoryDealInfo, HistoryOrderInfo, DBPositionsResponse, DBPositionInfo
)

def get_order_type_string(order_type: int) -> str:
    if order_type == mt5.ORDER_TYPE_BUY:
        return "buy"
    elif order_type == mt5.ORDER_TYPE_SELL:
        return "sell"
    elif order_type == mt5.ORDER_TYPE_BUY_LIMIT:
        return "buy_limit"
    elif order_type == mt5.ORDER_TYPE_SELL_LIMIT:
        return "sell_limit"
    elif order_type == mt5.ORDER_TYPE_BUY_STOP:
        return "buy_stop"
    elif order_type == mt5.ORDER_TYPE_SELL_STOP:
        return "sell_stop"
    return "unknown"

def get_all_positions() -> PositionsResponse:
    if not init_mt5():
        raise Exception("MT5 initialize failed")
    
    positions = get_positions()
    orders = mt5.orders_get()
    shutdown_mt5()
    
    pos_list = []
    
    if positions is not None and len(positions) > 0:
        for pos in positions:
            pos_type = get_order_type_string(pos.type)
            pos_list.append(PositionInfo(
                ticket=pos.ticket,
                time=pos.time,
                time_str=datetime.fromtimestamp(pos.time).strftime("%Y-%m-%d %H:%M:%S"),
                type=pos.type,
                type_str=pos_type,
                magic=pos.magic,
                identifier=pos.identifier,
                volume=pos.volume,
                price_open=pos.price_open,
                price_current=pos.price_current,
                sl=pos.sl,
                tp=pos.tp,
                profit=pos.profit,
                symbol=pos.symbol,
                comment=pos.comment
            ))
    
    if orders is not None and len(orders) > 0:
        for order in orders:
            order_type_str = get_order_type_string(order.type)
            order_time = getattr(order, 'time_setup', 0) if getattr(order, 'time_setup', 0) else 0
            pos_list.append(PositionInfo(
                ticket=order.ticket,
                time=order_time,
                time_str=datetime.fromtimestamp(order_time).strftime("%Y-%m-%d %H:%M:%S") if order_time > 0 else "",
                type=order.type,
                type_str=order_type_str,
                magic=order.magic,
                identifier=getattr(order, 'order_id', 0),
                volume=order.volume_current,
                price_open=order.price_open,
                price_current=order.price_current,
                sl=getattr(order, 'sl', 0),
                tp=getattr(order, 'tp', 0),
                profit=0.0,
                symbol=order.symbol,
                comment=order.comment
            ))
    
    return PositionsResponse(positions=pos_list, total=len(pos_list))

def open_market(request: OpenMarketRequest) -> ActionResponse:
    if not init_mt5():
        return ActionResponse(success=False, message="MT5 initialize failed")
    
    symbol_info = mt5.symbol_info(request.symbol)
    if symbol_info is None:
        shutdown_mt5()
        return ActionResponse(success=False, message=f"Symbol {request.symbol} not found")
    
    point = symbol_info.point
    if point == 0:
        shutdown_mt5()
        return ActionResponse(success=False, message=f"Invalid symbol {request.symbol}")
    
    symbol_digits = symbol_info.digits
    request.type = request.type.lower()
    
    if request.type == "buy":
        order_type = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(request.symbol).ask
    elif request.type == "sell":
        order_type = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(request.symbol).bid
    else:
        shutdown_mt5()
        return ActionResponse(success=False, message="Invalid order type")
    
    if request.sl is not None:
        request.sl = round(request.sl, symbol_digits)
    if request.tp is not None:
        request.tp = round(request.tp, symbol_digits)
    
    request.volume = round(request.volume, 2)
    
    request_dict = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": request.symbol,
        "volume": request.volume,
        "type": order_type,
        "price": price,
        "deviation": 20,
        "magic": request.magic,
        "comment": request.comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    if request.sl is not None:
        request_dict["sl"] = request.sl
    if request.tp is not None:
        request_dict["tp"] = request.tp
    
    result = mt5.order_send(request_dict)
    shutdown_mt5()
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        return ActionResponse(success=False, message=f"Order failed: {result.comment}")
    
    db = SessionLocal()
    try:
        new_position = Positions(
            ticket=result.order,
            symbol=request.symbol,
            type=request.type,
            volume=request.volume,
            price=price,
            sl=request.sl,
            tp=request.tp,
            profit=0,
            time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            is_running=1
        )
        db.add(new_position)
        db.commit()
    finally:
        db.close()
    
    return ActionResponse(success=True, message="Position opened", ticket=result.order)

def open_limit(request: OpenLimitRequest) -> ActionResponse:
    if not init_mt5():
        return ActionResponse(success=False, message="MT5 initialize failed")
    
    symbol_info = mt5.symbol_info(request.symbol)
    if symbol_info is None:
        shutdown_mt5()
        return ActionResponse(success=False, message=f"Symbol {request.symbol} not found")
    
    point = symbol_info.point
    if point == 0:
        shutdown_mt5()
        return ActionResponse(success=False, message=f"Invalid symbol {request.symbol}")
    
    symbol_digits = symbol_info.digits
    request.type = request.type.lower()
    
    if request.type == "buy":
        order_type = mt5.ORDER_TYPE_BUY_LIMIT
    elif request.type == "sell":
        order_type = mt5.ORDER_TYPE_SELL_LIMIT
    else:
        shutdown_mt5()
        return ActionResponse(success=False, message="Invalid order type")
    
    request.price = round(request.price, symbol_digits)
    if request.sl is not None:
        request.sl = round(request.sl, symbol_digits)
    if request.tp is not None:
        request.tp = round(request.tp, symbol_digits)
    
    request.volume = round(request.volume, 2)
    
    request_dict = {
        "action": mt5.TRADE_ACTION_PENDING,
        "symbol": request.symbol,
        "volume": request.volume,
        "type": order_type,
        "price": request.price,
        "deviation": 20,
        "magic": request.magic,
        "comment": request.comment,
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    if request.sl is not None:
        request_dict["sl"] = request.sl
    if request.tp is not None:
        request_dict["tp"] = request.tp
    
    result = mt5.order_send(request_dict)
    shutdown_mt5()
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        return ActionResponse(success=False, message=f"Order failed: {result.comment}")
    
    db = SessionLocal()
    try:
        new_position = Positions(
            ticket=result.order,
            symbol=request.symbol,
            type=request.type,
            volume=request.volume,
            price=request.price,
            sl=request.sl,
            tp=request.tp,
            profit=0,
            time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            is_running=2
        )
        db.add(new_position)
        db.commit()
    finally:
        db.close()
    
    return ActionResponse(success=True, message="Pending order placed", ticket=result.order)

def close_position_by_ticket(request: ClosePositionRequest) -> ActionResponse:
    if not init_mt5():
        return ActionResponse(success=False, message="MT5 initialize failed")
    
    positions = get_positions()
    orders = mt5.orders_get()
    
    position = None
    order = None
    
    if positions is not None:
        for pos in positions:
            if pos.ticket == request.ticket:
                position = pos
                break
    
    if orders is not None and position is None:
        for ord in orders:
            if ord.ticket == request.ticket:
                order = ord
                break
    
    if position is None and order is None:
        shutdown_mt5()
        return ActionResponse(success=False, message=f"Position {request.ticket} not found")
    
    if order is not None:
        delete_request = {
            "action": mt5.TRADE_ACTION_REMOVE,
            "order": request.ticket,
            "type": mt5.ORDER_TYPE_SELL,
        }
        result = mt5.order_send(delete_request)
        shutdown_mt5()
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            return ActionResponse(success=False, message=f"Delete order failed: {result.comment}")
        
        db = SessionLocal()
        try:
            pos = db.query(Positions).filter(Positions.ticket == request.ticket).first()
            if pos:
                pos.is_running = 0
                pos.closed_by = "manual"
                db.commit()
        finally:
            db.close()
        
        return ActionResponse(success=True, message=f"Order {request.ticket} deleted", ticket=request.ticket)
    
    symbol_info = mt5.symbol_info(position.symbol)
    if symbol_info is None:
        shutdown_mt5()
        return ActionResponse(success=False, message=f"Symbol {position.symbol} not found")
    
    point = symbol_info.point
    if point == 0:
        shutdown_mt5()
        return ActionResponse(success=False, message=f"Invalid symbol {position.symbol}")
    
    symbol_digits = symbol_info.digits
    order_type = mt5.ORDER_TYPE_SELL if position.type == 0 else mt5.ORDER_TYPE_BUY
    price = mt5.symbol_info_tick(position.symbol).bid if position.type == 0 else mt5.symbol_info_tick(position.symbol).ask
    
    request_dict = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": position.symbol,
        "volume": position.volume,
        "type": order_type,
        "price": price,
        "deviation": 20,
        "magic": position.magic,
        "comment": f"Close {request.ticket}",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
        "position": request.ticket,
    }
    
    result = mt5.order_send(request_dict)
    shutdown_mt5()
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        return ActionResponse(success=False, message=f"Close failed: {result.comment}")
    
    db = SessionLocal()
    try:
        pos = db.query(Positions).filter(Positions.ticket == request.ticket).first()
        if pos:
            pos.is_running = 0
            pos.profit = position.profit
            pos.closed_by = "manual"
            db.commit()
    finally:
        db.close()
    
    return ActionResponse(success=True, message=f"Position {request.ticket} closed", ticket=request.ticket)

def close_all_positions_controller():
    if not init_mt5():
        return ActionResponse(success=False, message="MT5 initialize failed")
    
    result = mt5_close_all_positions()
    shutdown_mt5()
    
    if result is None:
        return ActionResponse(success=False, message="Failed to close positions")
    
    db = SessionLocal()
    try:
        db.query(Positions).filter(Positions.is_running == 1).update({
            Positions.is_running: 0,
            Positions.closed_by: "close_all"
        })
        db.commit()
    finally:
        db.close()
    
    return ActionResponse(success=True, message=f"Closed {len(result)} positions")

def modify_position(request: ModifyPositionRequest) -> ActionResponse:
    if not init_mt5():
        return ActionResponse(success=False, message="MT5 initialize failed")
    
    positions = get_positions()
    orders = mt5.orders_get()
    
    position = None
    order = None
    
    if positions is not None:
        for pos in positions:
            if pos.ticket == request.ticket:
                position = pos
                break
    
    if orders is not None and position is None:
        for ord in orders:
            if ord.ticket == request.ticket:
                order = ord
                break
    
    if position is None and order is None:
        shutdown_mt5()
        return ActionResponse(success=False, message=f"Position {request.ticket} not found")
    
    if order is not None:
        symbol_info = mt5.symbol_info(order.symbol)
        if symbol_info is None:
            shutdown_mt5()
            return ActionResponse(success=False, message=f"Symbol {order.symbol} not found")
        
        symbol_digits = symbol_info.digits
        sl = getattr(order, 'sl', 0)
        tp = getattr(order, 'tp', 0)
        volume = order.volume_current
        price = order.price_open
        order_type = order.type
        
        if request.sl is not None:
            sl = round(request.sl, symbol_digits)
        if request.tp is not None:
            tp = round(request.tp, symbol_digits)
        if request.volume is not None:
            volume = round(request.volume, 2)
        
        modify_request = {
            "action": mt5.TRADE_ACTION_MODIFY,
            "symbol": order.symbol,
            "order": request.ticket,
            "price": price,
            "sl": sl,
            "tp": tp,
            "volume": volume,
            "type": order_type,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

    elif position is not None:
        symbol_info = mt5.symbol_info(position.symbol)
        if symbol_info is None:
            shutdown_mt5()
            return ActionResponse(success=False, message=f"Symbol {position.symbol} not found")

        symbol_digits = symbol_info.digits
        sl = position.sl
        tp = position.tp

        if request.sl is not None:
            sl = round(request.sl, symbol_digits)
        if request.tp is not None:
            tp = round(request.tp, symbol_digits)

        if request.volume is not None:
            shutdown_mt5()
            return ActionResponse(success=False, message="Cannot modify volume for open positions")

        modify_request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": position.symbol,
            "sl": sl,
            "tp": tp,
            "position": request.ticket,
        }

    result = mt5.order_send(modify_request)
    shutdown_mt5()
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        return ActionResponse(success=False, message=f"Modify order failed: {result.comment}")
    
    db = SessionLocal()
    try:
        pos = db.query(Positions).filter(Positions.ticket == request.ticket).first()
        if pos:
            if request.sl is not None:
                pos.sl = request.sl
            if request.tp is not None:
                pos.tp = request.tp
            if request.volume is not None:
                pos.volume = request.volume
            db.commit()
    finally:
        db.close()
    
    return ActionResponse(success=True, message=f"Order {request.ticket} modified", ticket=request.ticket)
    
    symbol_info = mt5.symbol_info(position.symbol)
    if symbol_info is None:
        shutdown_mt5()
        return ActionResponse(success=False, message=f"Symbol {position.symbol} not found")
    
    symbol_digits = symbol_info.digits
    sl = position.sl
    tp = position.tp
    volume = position.volume
    
    if request.sl is not None:
        sl = round(request.sl, symbol_digits)
    if request.tp is not None:
        tp = round(request.tp, symbol_digits)
    if request.volume is not None:
        volume = round(request.volume, 2)
    
    modify_request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "symbol": position.symbol,
        "position": request.ticket,
        "sl": sl,
        "tp": tp,
        "volume": volume,
    }
    
    result = mt5.order_send(modify_request)
    shutdown_mt5()
    
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        return ActionResponse(success=False, message=f"Modify failed: {result.comment}")
    
    db = SessionLocal()
    try:
        pos = db.query(Positions).filter(Positions.ticket == request.ticket).first()
        if pos:
            if request.sl is not None:
                pos.sl = request.sl
            if request.tp is not None:
                pos.tp = request.tp
            if request.volume is not None:
                pos.volume = request.volume
            db.commit()
    finally:
        db.close()
    
    return ActionResponse(success=True, message=f"Position {request.ticket} modified", ticket=request.ticket)

def get_history(from_date: str, to_date: str) -> HistoryResponse:
    if not init_mt5():
        raise Exception("MT5 initialize failed")
    
    from_dt = datetime.strptime(from_date, "%d%m%Y")
    to_dt = datetime.strptime(to_date, "%d%m%Y")
    from_ts = int(from_dt.timestamp())
    to_ts = int(to_dt.timestamp())
    
    deals = get_history_deals(from_ts, to_ts)
    orders = get_history_orders(from_ts, to_ts)
    
    shutdown_mt5()
    
    deal_list = []
    if deals is not None and len(deals) > 0:
        for deal in deals:
            if not deal.symbol:
                continue
            deal_type_str = "deal_unknown"
            if deal.type == mt5.DEAL_TYPE_BUY:
                deal_type_str = "buy"
            elif deal.type == mt5.DEAL_TYPE_SELL:
                deal_type_str = "sell"
            elif deal.type == mt5.DEAL_TYPE_BALANCE:
                deal_type_str = "balance"
            elif deal.type == mt5.DEAL_TYPE_CREDIT:
                deal_type_str = "credit"
            elif deal.type == mt5.DEAL_TYPE_CHARGE:
                deal_type_str = "charge"
            elif deal.type == mt5.DEAL_TYPE_DIVIDEND:
                deal_type_str = "dividend"
            elif deal.type == mt5.DEAL_TYPE_WITHDRAWAL:
                deal_type_str = "withdrawal"
            elif deal.type == mt5.DEAL_TYPE_DEALER:
                deal_type_str = "dealer"
            
            deal_list.append(HistoryDealInfo(
                ticket=deal.ticket,
                time=deal.time,
                time_str=datetime.fromtimestamp(deal.time).strftime("%Y-%m-%d %H:%M:%S"),
                time_msc=deal.time_msc,
                type=deal.type,
                type_str=deal_type_str,
                magic=deal.magic,
                order=deal.order,
                position_id=deal.position_id,
                volume=deal.volume,
                price=deal.price,
                sl=getattr(deal, 'sl', 0.0),
                tp=getattr(deal, 'tp', 0.0),
                commission=deal.commission,
                fee=getattr(deal, 'fee', 0.0),
                profit=deal.profit,
                symbol=deal.symbol,
                comment=deal.comment,
                external_id=getattr(deal, 'external_id', '')
            ))
    
    order_list = []
    if orders is not None and len(orders) > 0:
        for order in orders:
            if not order.symbol:
                continue
            order_type_str = get_order_type_string(order.type)
            time_setup = getattr(order, 'time_setup', 0)
            order_list.append(HistoryOrderInfo(
                ticket=order.ticket,
                time_setup=time_setup,
                time_setup_str=datetime.fromtimestamp(time_setup).strftime("%Y-%m-%d %H:%M:%S") if time_setup > 0 else "",
                time_expiration=getattr(order, 'time_expiration', 0),
                type=order.type,
                type_str=order_type_str,
                magic=order.magic,
                volume_current=order.volume_current,
                volume_original=getattr(order, 'volume_initial', order.volume_current),
                price_open=order.price_open,
                price_current=order.price_current,
                sl=order.sl,
                tp=order.tp,
                position_id=getattr(order, 'position_id', 0),
                comment=order.comment
            ))
    
    return HistoryResponse(
        deals=deal_list,
        orders=order_list,
        total_deals=len(deal_list),
        total_orders=len(order_list)
    )

def get_history_today():
    from datetime import timedelta
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    start_date = today.strftime("%d%m%Y")
    end_date = tomorrow.strftime("%d%m%Y")
    return get_history(start_date, end_date)

def get_db_positions(page: int = 1, per_page: int = 20, is_running: Optional[int] = None) -> DBPositionsResponse:
    db = SessionLocal()
    try:
        query = db.query(Positions)
        
        if is_running is not None:
            query = query.filter(Positions.is_running == is_running)
        
        total = query.count()
        total_pages = (total + per_page - 1) // per_page
        
        positions = query.order_by(Positions.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        pos_list = []
        for pos in positions:
            pos_list.append(DBPositionInfo(
                id=pos.id,
                ticket=pos.ticket,
                symbol=pos.symbol,
                type=pos.type,
                volume=float(pos.volume) if pos.volume else 0,
                price=float(pos.price) if pos.price else 0,
                sl=float(pos.sl) if pos.sl else None,
                tp=float(pos.tp) if pos.tp else None,
                profit=float(pos.profit) if pos.profit else 0,
                closed_by=pos.closed_by,
                time=pos.time,
                is_running=pos.is_running,
                created_at=pos.created_at.strftime("%Y-%m-%d %H:%M:%S") if pos.created_at else None,
                updated_at=pos.updated_at.strftime("%Y-%m-%d %H:%M:%S") if pos.updated_at else None
            ))
        
        return DBPositionsResponse(
            positions=pos_list,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
    finally:
        db.close()

def get_db_positions_today(page: int = 1, per_page: int = 20) -> DBPositionsResponse:
    db = SessionLocal()
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        
        query = db.query(Positions).filter(Positions.time.startswith(today))
        
        total = query.count()
        total_pages = (total + per_page - 1) // per_page
        
        positions = query.order_by(Positions.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
        
        pos_list = []
        for pos in positions:
            pos_list.append(DBPositionInfo(
                id=pos.id,
                ticket=pos.ticket,
                symbol=pos.symbol,
                type=pos.type,
                volume=float(pos.volume) if pos.volume else 0,
                price=float(pos.price) if pos.price else 0,
                sl=float(pos.sl) if pos.sl else None,
                tp=float(pos.tp) if pos.tp else None,
                profit=float(pos.profit) if pos.profit else 0,
                closed_by=pos.closed_by,
                time=pos.time,
                is_running=pos.is_running,
                created_at=pos.created_at.strftime("%Y-%m-%d %H:%M:%S") if pos.created_at else None,
                updated_at=pos.updated_at.strftime("%Y-%m-%d %H:%M:%S") if pos.updated_at else None
            ))
        
        return DBPositionsResponse(
            positions=pos_list,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
    finally:
        db.close()