from typing import Optional
from fastapi import APIRouter, Query

router = APIRouter()

TABLE_MAP = {
    "M1": "swings_m1",
    "M5": "swings_m5",
    "M15": "swings_m15",
    "H1": "swings_h1",
}

def get_swings(
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
                SELECT id, symbol, type, price, timestamp, strength, distance, is_confirmed, created_at
                FROM {table_name}
                WHERE {where_sql}
                ORDER BY timestamp DESC
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
                SELECT id, symbol, type, price, timestamp, strength, distance, is_confirmed, created_at
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
async def get_swings_charts(
    timeframe: str,
    symbol: Optional[str] = Query(None, description="Filter by symbol")
):
    from app.databases.config import SessionLocal
    from sqlalchemy import text
    
    table_name = TABLE_MAP.get(timeframe.upper())
    if not table_name:
        return []
        
    db = SessionLocal()
    try:
        result = db.execute(text(f"""
            SELECT timestamp, price, type
            FROM {table_name}
            WHERE symbol = :symbol
            ORDER BY timestamp ASC
        """), {"symbol": symbol}).fetchall()
        
        output = []
        for row in result:
            try:
                if not row[0] or not row[1]:
                    continue
                    
                time = int(row[0].timestamp()) if hasattr(row[0], 'timestamp') else int(row[0])
                price = float(row[1])
                
                if time <= 0 or price <= 0:
                    continue
                    
                output.append({
                    "time": time,
                    "price": price,
                    "type": row[2]
                })
            except:
                continue
        
        return output[-200:]
    except:
        return []
    finally:
        db.close()

@router.get("/{timeframe}")
async def get_swings_route(
    timeframe: str,
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100)
):
    return get_swings(timeframe, symbol, page, limit)