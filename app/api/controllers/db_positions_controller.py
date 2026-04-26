from typing import Optional
from datetime import datetime
from app.databases.config import SessionLocal
from app.databases.models.positions_model import Positions
from app.api.models.position_model import DBPositionsResponse, DBPositionInfoRaw

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
            time_val = pos.time
            if isinstance(time_val, datetime):
                time_val = time_val.strftime("%Y-%m-%d %H:%M:%S")
            elif time_val is None:
                time_val = None
                
            pos_list.append(DBPositionInfoRaw(
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
                time=time_val,
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
            time_val = pos.time
            if isinstance(time_val, datetime):
                time_val = time_val.strftime("%Y-%m-%d %H:%M:%S")
            elif time_val is None:
                time_val = None
                
            pos_list.append(DBPositionInfoRaw(
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
                time=time_val,
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
