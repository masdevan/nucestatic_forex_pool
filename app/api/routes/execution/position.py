from fastapi import APIRouter, Query
from app.databases.config import SessionLocal
from sqlalchemy import text

router = APIRouter()

@router.get("/position_total")
async def get_execution_position_total(
    symbol: str = Query(..., description="Symbol to check for running positions")
):
    db = SessionLocal()
    try:
        positions = db.execute(text("""
            SELECT ticket, type, volume, sl, tp, price
            FROM positions
            WHERE symbol = :symbol AND is_running = 1
            ORDER BY time DESC
        """), {"symbol": symbol}).fetchall()

        total = len(positions)
        
        running_list = []
        for pos in positions:
            running_list.append({
                "ticket": pos[0],
                "type": pos[1],
                "volume": float(pos[2]) if pos[2] else 0,
                "sl": float(pos[3]) if pos[3] else 0,
                "tp": float(pos[4]) if pos[4] else 0,
                "entry_price": float(pos[5]) if pos[5] else 0
            })

        return {
            "symbol": symbol,
            "running_positions": total,
            "has_running": total > 0,
            "positions": running_list
        }

    finally:
        db.close()
