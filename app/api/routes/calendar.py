from fastapi import APIRouter, Query
from datetime import datetime, timedelta
from app.databases.config import SessionLocal
from app.databases.models.calendar_model import Calendar

router = APIRouter()

def get_today_range():
    """Get today's date range (00:00 to 23:59)"""
    today = datetime.now()
    start = today.replace(hour=0, minute=0, second=0, microsecond=0)
    end = today.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start, end

@router.get("/calendar/today")
def get_calendar_today():
    db = SessionLocal()
    try:
        start, end = get_today_range()
        
        items = db.query(Calendar).filter(
            Calendar.time >= start,
            Calendar.time <= end
        ).order_by(Calendar.time.asc()).all()
        
        return {
            "data": [ {
                "id": item.id,
                "time": item.time,
                "currency": item.currency,
                "event": item.event,
                "url": item.url,
                "impact": item.impact,
                "actual": item.actual,
                "forecast": item.forecast,
                "previous": item.previous,
                "description": item.description,
                "description_status": item.description_status
            } for item in items ]
        }
    finally:
        db.close()

@router.get("/calendar")
def get_calendar(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    currency: str = Query(None),
    impact: str = Query(None),
    start_date: str = Query(None),
    end_date: str = Query(None)
):
    db = SessionLocal()
    try:
        query = db.query(Calendar)
        
        if currency:
            query = query.filter(Calendar.currency == currency.upper())
        
        if impact:
            query = query.filter(Calendar.impact == impact.lower())
        
        if start_date:
            query = query.filter(Calendar.time >= start_date)
        
        if end_date:
            query = query.filter(Calendar.time <= end_date)
        
        total = query.count()
        
        offset = (page - 1) * limit
        items = query.order_by(Calendar.time.desc()).offset(offset).limit(limit).all()
        
        total_pages = (total + limit - 1) // limit
        
        return {
            "data": [ {
                "id": item.id,
                "time": item.time,
                "currency": item.currency,
                "event": item.event,
                "url": item.url,
                "impact": item.impact,
                "actual": item.actual,
                "forecast": item.forecast,
                "previous": item.previous,
                "description": item.description,
                "description_status": item.description_status
            } for item in items ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            },
            "filters": {
                "currency": currency,
                "impact": impact,
                "start_date": start_date,
                "end_date": end_date
            }
        }
    finally:
        db.close()
