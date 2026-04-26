from fastapi import APIRouter, HTTPException, Query
from app.api.models.position_model import (
    PositionsResponse, OpenMarketRequest, OpenLimitRequest, 
    ClosePositionRequest, ModifyPositionRequest, ActionResponse, 
    HistoryResponse, DBPositionsResponse, DBPositionInfoRaw
)
from app.api.controllers.position_controller import (
    open_market, open_limit, close_position_by_ticket, 
    close_all_positions_controller, modify_position, get_history, get_history_today
)
from app.api.controllers.db_positions_controller import get_db_positions, get_db_positions_today

router = APIRouter()

@router.get("", response_model=PositionsResponse)
async def get_positions():
    try:
        from app.api.controllers.position_controller import get_all_positions
        return get_all_positions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/open/market", response_model=ActionResponse)
async def open_market_route(request: OpenMarketRequest):
    return open_market(request)

@router.post("/open/limit", response_model=ActionResponse)
async def open_limit_route(request: OpenLimitRequest):
    return open_limit(request)

@router.post("/close", response_model=ActionResponse)
async def close_position_route(request: ClosePositionRequest):
    return close_position_by_ticket(request)

@router.post("/close_all", response_model=ActionResponse)
async def close_all_positions_route():
    return close_all_positions_controller()

@router.post("/modify", response_model=ActionResponse)
async def modify_position_route(request: ModifyPositionRequest):
    return modify_position(request)

@router.get("/history", response_model=HistoryResponse)
async def get_history_route(from_date: str, to_date: str):
    return get_history(from_date, to_date)

@router.get("/history/today", response_model=HistoryResponse)
async def get_history_today_route():
    return get_history_today()

@router.get("/db", response_model=DBPositionsResponse)
async def get_db_positions_route(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    is_running: int = Query(None, description="1=running, 0=closed, 2=pending")
):
    try:
        return get_db_positions(page=page, per_page=per_page, is_running=is_running)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/db/today", response_model=DBPositionsResponse)
async def get_db_positions_today_route(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100)
):
    try:
        return get_db_positions_today(page=page, per_page=per_page)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chart/history")
async def get_positions_chart_history(symbol: str):
    from app.databases.config import SessionLocal
    from sqlalchemy import text
    
    db = SessionLocal()
    try:
        positions = db.execute(text("""
            SELECT 
                time,
                updated_at,
                type,
                price,
                sl,
                tp,
                profit,
                closed_by
            FROM positions 
            WHERE symbol = :symbol 
              AND is_running = 0
              AND updated_at IS NOT NULL
            ORDER BY time ASC
        """), {"symbol": symbol}).fetchall()
        
        result = []
        for pos in positions:
            try:
                entry_time = int(pos[0].timestamp()) if pos[0] else None
                exit_time = int(pos[1].timestamp()) if pos[1] else entry_time
                
                result.append({
                    "entry_time": entry_time,
                    "exit_time": exit_time,
                    "type": pos[2],
                    "entry_price": float(pos[3] or 0),
                    "sl": float(pos[4] or 0),
                    "tp": float(pos[5] or 0),
                    "profit": float(pos[6] or 0),
                    "result": "tp" if pos[7] == "tp" else "sl"
                })
            except:
                continue
        
        return result
    finally:
        db.close()

@router.get("/performance")
async def get_performance_stats():
    from app.databases.config import SessionLocal
    from sqlalchemy import text
    from datetime import datetime, timedelta
    
    db = SessionLocal()
    try:
        symbols = db.execute(text("SELECT DISTINCT symbol FROM positions WHERE is_running = 0")).fetchall()
        symbols = [s[0] for s in symbols]
        
        result = {}
        
        for symbol in symbols:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            daily = db.execute(text("""
                SELECT SUM(profit) as total, COUNT(*) as count
                FROM positions 
                WHERE symbol = :symbol AND is_running = 0 AND time >= :today
            """), {"symbol": symbol, "today": today}).fetchone() or (0, 0)
            
            week_ago = today - timedelta(days=7)
            weekly = db.execute(text("""
                SELECT SUM(profit) as total, COUNT(*) as count
                FROM positions 
                WHERE symbol = :symbol AND is_running = 0 AND time >= :week_ago
            """), {"symbol": symbol, "week_ago": week_ago}).fetchone() or (0, 0)
            
            month_ago = today - timedelta(days=30)
            monthly = db.execute(text("""
                SELECT SUM(profit) as total, COUNT(*) as count
                FROM positions 
                WHERE symbol = :symbol AND is_running = 0 AND time >= :month_ago
            """), {"symbol": symbol, "month_ago": month_ago}).fetchone() or (0, 0)
            
            year_ago = today - timedelta(days=365)
            yearly = db.execute(text("""
                SELECT SUM(profit) as total, COUNT(*) as count
                FROM positions 
                WHERE symbol = :symbol AND is_running = 0 AND time >= :year_ago
            """), {"symbol": symbol, "year_ago": year_ago}).fetchone() or (0, 0)
            
            win_loss = db.execute(text("""
                SELECT 
                    SUM(CASE WHEN profit > 0 THEN profit ELSE 0 END) as profit_total,
                    SUM(CASE WHEN profit < 0 THEN profit ELSE 0 END) as loss_total,
                    COUNT(CASE WHEN profit > 0 THEN 1 END) as wins,
                    COUNT(CASE WHEN profit < 0 THEN 1 END) as losses
                FROM positions 
                WHERE symbol = :symbol AND is_running = 0
            """), {"symbol": symbol}).fetchone() or (0, 0, 0, 0)
            
            result[symbol] = {
                "daily": {
                    "profit": float(daily[0] or 0),
                    "trades": int(daily[1] or 0)
                },
                "weekly": {
                    "profit": float(weekly[0] or 0),
                    "trades": int(weekly[1] or 0)
                },
                "monthly": {
                    "profit": float(monthly[0] or 0),
                    "trades": int(monthly[1] or 0)
                },
                "yearly": {
                    "profit": float(yearly[0] or 0),
                    "trades": int(yearly[1] or 0)
                },
                "overall": {
                    "total_profit": float(win_loss[0] or 0),
                    "total_loss": float(win_loss[1] or 0),
                    "net_profit": float((win_loss[0] or 0) + (win_loss[1] or 0)),
                    "wins": int(win_loss[2] or 0),
                    "losses": int(win_loss[3] or 0),
                    "win_rate": round((int(win_loss[2] or 0) / max((int(win_loss[2] or 0) + int(win_loss[3] or 0)), 1)) * 100, 2)
                }
            }
        
        symbol_count = len(result)
        
        if symbol_count > 0:
            total_daily = sum(s['daily']['profit'] for s in result.values())
            total_weekly = sum(s['weekly']['profit'] for s in result.values())
            total_monthly = sum(s['monthly']['profit'] for s in result.values())
            total_yearly = sum(s['yearly']['profit'] for s in result.values())
            
            total_wins = sum(s['overall']['wins'] for s in result.values())
            total_losses = sum(s['overall']['losses'] for s in result.values())
            total_profit = sum(s['overall']['total_profit'] for s in result.values())
            total_loss = sum(s['overall']['total_loss'] for s in result.values())
            
            result['_total'] = {
                "daily": {
                    "profit": total_daily,
                    "trades": sum(s['daily']['trades'] for s in result.values())
                },
                "weekly": {
                    "profit": total_weekly,
                    "trades": sum(s['weekly']['trades'] for s in result.values())
                },
                "monthly": {
                    "profit": total_monthly,
                    "trades": sum(s['monthly']['trades'] for s in result.values())
                },
                "yearly": {
                    "profit": total_yearly,
                    "trades": sum(s['yearly']['trades'] for s in result.values())
                },
                "overall": {
                    "total_profit": total_profit,
                    "total_loss": total_loss,
                    "net_profit": total_profit + total_loss,
                    "wins": total_wins,
                    "losses": total_losses,
                    "win_rate": round((total_wins / max(total_wins + total_losses, 1)) * 100, 2)
                }
            }
            
            avg_daily = total_daily / symbol_count
            avg_weekly = total_weekly / symbol_count
            avg_monthly = total_monthly / symbol_count
            avg_yearly = total_yearly / symbol_count
            
            avg_win_rate = sum(s['overall']['win_rate'] for s in result.values()) / symbol_count
            
            result['_average'] = {
                "daily": {
                    "profit": avg_daily,
                    "trades": int(result['_total']['daily']['trades'] / symbol_count)
                },
                "weekly": {
                    "profit": avg_weekly,
                    "trades": int(result['_total']['weekly']['trades'] / symbol_count)
                },
                "monthly": {
                    "profit": avg_monthly,
                    "trades": int(result['_total']['monthly']['trades'] / symbol_count)
                },
                "yearly": {
                    "profit": avg_yearly,
                    "trades": int(result['_total']['yearly']['trades'] / symbol_count)
                },
                "overall": {
                    "win_rate": round(avg_win_rate, 2),
                    "wins": int(total_wins / symbol_count),
                    "losses": int(total_losses / symbol_count)
                }
            }
        
        return result
    finally:
        db.close()

