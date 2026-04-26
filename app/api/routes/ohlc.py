import os
from typing import Optional
from fastapi import APIRouter, Query
from app.api.models.ohlc_model import OHLCResponse
from app.api.controllers.ohlc_controller import get_ohlc_data as controller_get_ohlc, get_ohlc_today, get_ohlc_all

router = APIRouter()

PAIRS = [p.strip() for p in os.getenv("TRADE_PAIR", "USDJPYm").split(",") if p.strip()]

TABLE_MAP = {
    "M1": "ohlc_m1",
    "M5": "ohlc_m5",
    "M15": "ohlc_m15",
    "H1": "ohlc_h1",
}

def get_ohlc_with_filters(
    timeframe: str,
    symbol: Optional[str] = None,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
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

        if start_time:
            where_clauses.append("time >= :start_time")
            params["start_time"] = start_time

        if end_time:
            where_clauses.append("time <= :end_time")
            params["end_time"] = end_time

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        if limit is not None:
            params["limit"] = limit
            params["offset"] = (page - 1) * limit
            query = text(f"""
                SELECT symbol, time, time_str, session, is_done, open, high, low, close, tick_volume, atr, sweep_high, sweep_low, sweep_strength
                FROM {table_name}
                WHERE {where_sql}
                ORDER BY time DESC
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
                SELECT symbol, time, time_str, session, is_done, open, high, low, close, tick_volume, atr, sweep_high, sweep_low, sweep_strength
                FROM {table_name}
                WHERE {where_sql}
                ORDER BY time ASC
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

@router.get("/pairs")
async def get_pairs():
    return {"pairs": PAIRS}

@router.get("")
async def get_ohlc_data(
    pair: str = Query(...),
    timeframe: str = Query(...),
    start_date: str = Query(...),
    end_date: str = Query(...)
):
    return controller_get_ohlc(pair, timeframe, start_date, end_date)

@router.get("/today", response_model=OHLCResponse)
async def get_ohlc_today_route(
    pair: str = Query(...),
    timeframe: str = Query(...)
):
    return get_ohlc_today(pair, timeframe)

@router.get("/all")
async def get_ohlc_all_route(
    pair: str = Query(...)
):
    return get_ohlc_all(pair)

@router.get("/charts/{timeframe}")
async def get_ohlc_charts(
    timeframe: str,
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    start_time: Optional[int] = Query(None, description="Filter by start time (Unix timestamp)"),
    end_time: Optional[int] = Query(None, description="Filter by end time (Unix timestamp)")
):
    return get_ohlc_with_filters(timeframe, symbol, start_time, end_time, page=1, limit=None)

@router.get("/{timeframe}")
async def get_ohlc(
    timeframe: str,
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    start_time: Optional[int] = Query(None, description="Filter by start time (Unix timestamp)"),
    end_time: Optional[int] = Query(None, description="Filter by end time (Unix timestamp)"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100)
):
    return get_ohlc_with_filters(timeframe, symbol, start_time, end_time, page, limit)