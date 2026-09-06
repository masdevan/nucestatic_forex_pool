from typing import Optional
from fastapi import APIRouter, Query

router = APIRouter()

TIMEFRAME_LIST = ["m1", "m5", "m15", "m30", "h1", "h4", "d1", "w1", "mn1"]


def get_ohlc_with_filters(
    timeframe: str,
    symbol: str,
    start_time: Optional[int] = None,
    end_time: Optional[int] = None,
    page: int = 1,
    limit: Optional[int] = 50
):
    from app.databases.config import SessionLocal
    from sqlalchemy import text

    table_name = f"ohlc_{symbol.lower()}_{timeframe.lower()}"

    db = SessionLocal()
    try:
        check = db.execute(text(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema = DATABASE() AND table_name = :tbl"
        ), {"tbl": table_name}).scalar()
        if not check:
            return {"data": [], "pagination": {"page": 1, "limit": limit or 50, "total": 0, "total_pages": 0, "has_next": False, "has_prev": False}}

        where_clauses = ["symbol = :symbol"]
        params = {"symbol": symbol}

        if start_time:
            where_clauses.append("time >= :start_time")
            params["start_time"] = start_time

        if end_time:
            where_clauses.append("time <= :end_time")
            params["end_time"] = end_time

        where_sql = " AND ".join(where_clauses)

        if limit is not None:
            params["limit"] = limit
            params["offset"] = (page - 1) * limit
            query = text(f"""
                SELECT symbol, time, open, high, low, close
                FROM `{table_name}`
                WHERE {where_sql}
                ORDER BY time DESC
                LIMIT :limit OFFSET :offset
            """)
            rows = db.execute(query, params).fetchall()

            total = db.execute(
                text(f"SELECT COUNT(*) FROM `{table_name}` WHERE {where_sql}"), params
            ).scalar()

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
                SELECT symbol, time, open, high, low, close
                FROM `{table_name}`
                WHERE {where_sql}
                ORDER BY time ASC
            """)
            rows = db.execute(query, params).fetchall()

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


@router.get("/{timeframe}")
async def get_ohlc(
    timeframe: str,
    symbol: str = Query(..., description="Symbol name"),
    start_time: Optional[int] = Query(None, description="Start time (Unix timestamp)"),
    end_time: Optional[int] = Query(None, description="End time (Unix timestamp)"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100)
):
    return get_ohlc_with_filters(timeframe, symbol, start_time, end_time, page, limit)
