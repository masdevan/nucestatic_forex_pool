from fastapi import APIRouter, Query
from app.databases.config import SessionLocal
from sqlalchemy import text
from datetime import datetime

router = APIRouter()

@router.get("/total_loss_today")
async def get_execution_total_loss_today(
    symbol: str = Query(..., description="Symbol to calculate today's total loss")
):
    db = SessionLocal()
    try:
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        trades = db.execute(text("""
            SELECT profit
            FROM positions
            WHERE symbol = :symbol
              AND is_running = 0
              AND time >= :today_start
            ORDER BY time DESC
        """), {"symbol": symbol, "today_start": today_start}).fetchall()
        
        consecutive_loss = 0
        three_consecutive_loss = False
        
        if trades:
            for trade in trades:
                if trade is None:
                    continue
                profit = float(trade[0] or 0)
                if profit < 0:
                    consecutive_loss += 1
                    if consecutive_loss >= 3:
                        three_consecutive_loss = True
                        break
                else:
                    break  
        
        total_loss_today = 0.0
        if trades:
            total_loss_today = abs(sum(float(t[0]) for t in trades if t is not None and float(t[0] or 0) < 0))
        
        valid = not three_consecutive_loss
        
        return {
            "symbol": symbol,
            "valid": valid,
            "three_consecutive_loss": three_consecutive_loss,
            "consecutive_loss_count": consecutive_loss,
            "total_loss_today": round(total_loss_today, 2)
        }
        
    finally:
        db.close()
