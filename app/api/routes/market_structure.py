from typing import Optional
from fastapi import APIRouter, Query

router = APIRouter()

TABLE_MAP = {
    "M1": "market_structure_m1",
    "M5": "market_structure_m5",
    "M15": "market_structure_m15",
    "H1": "market_structure_h1",
}

def get_market_structure(
    timeframe: str,
    symbol: Optional[str] = None,
    page: int = 1,
    limit: Optional[int] = 50
):
    from app.databases.config import SessionLocal
    from sqlalchemy import text

    table_name = TABLE_MAP.get(timeframe.upper())
    if not table_name:
        return {"data": [], "pagination": {"page": 1, "limit": limit or 50, "total": 0, "total_pages": 0, "has_next": False, "has_prev": False}}

    db = SessionLocal()
    try:
        where_clauses = []
        params = {}

        if symbol:
            where_clauses.append("symbol = :symbol")
            params["symbol"] = symbol

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        if limit is not None:
            params["limit"] = limit
            params["offset"] = (page - 1) * limit
            query = text(f"""
                SELECT symbol, timeframe, structure_type, label, is_break_structure,
                       previous_swing_high_price, previous_swing_high_time,
                       current_swing_high_price, current_swing_high_time,
                       previous_swing_low_price, previous_swing_low_time,
                       current_swing_low_price, current_swing_low_time,
                       duration_seconds, trend_bias, continuation, speed, move_size,
                       liquidity_sweep, max_sweep_strength, sweep_high_count, sweep_low_count
                FROM {table_name}
                WHERE {where_sql}
                ORDER BY id DESC
                LIMIT :limit OFFSET :offset
            """)
            result = db.execute(query, params)
            rows = result.fetchall()

            count_query = text(f"SELECT COUNT(*) FROM {table_name} WHERE {where_sql}")
            count_result = db.execute(count_query, params)
            total = count_result.scalar()

            total_pages = (total + limit - 1) // limit if total else 0

            pagination = {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        else:
            query = text(f"""
                SELECT symbol, timeframe, structure_type, label, is_break_structure,
                       previous_swing_high_price, previous_swing_high_time,
                       current_swing_high_price, current_swing_high_time,
                       previous_swing_low_price, previous_swing_low_time,
                       current_swing_low_price, current_swing_low_time,
                       duration_seconds, trend_bias, continuation, speed, move_size,
                       liquidity_sweep, max_sweep_strength, sweep_high_count, sweep_low_count
                FROM {table_name}
                WHERE {where_sql}
                ORDER BY id ASC
            """)
            result = db.execute(query, params)
            rows = result.fetchall()

            pagination = {
                "page": 1,
                "limit": len(rows),
                "total": len(rows),
                "total_pages": 1,
                "has_next": False,
                "has_prev": False
            }

        return {
            "data": [dict(row._mapping) for row in rows],
            "pagination": pagination
        }
    finally:
        db.close()

@router.get("/charts/{timeframe}")
async def get_market_structure_charts(
    timeframe: str,
    symbol: Optional[str] = Query(None, description="Filter by symbol")
):
    return get_market_structure(timeframe, symbol, page=1, limit=None)

@router.get("/{timeframe}")
async def get_market_structure_route(
    timeframe: str,
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100)
):
    return get_market_structure(timeframe, symbol, page, limit)