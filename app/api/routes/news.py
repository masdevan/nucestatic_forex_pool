from fastapi import APIRouter, Query
from datetime import date, datetime
from app.databases.config import SessionLocal
from app.databases.models.news_model import News
from sqlalchemy import func

router = APIRouter()

@router.get("/news")
def get_news(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    news_date: str = Query(None)
):
    db = SessionLocal()
    try:
        query = db.query(News)
        
        if news_date:
            query = query.filter(News.time == news_date)
        
        total = query.count()
        
        offset = (page - 1) * limit
        items = query.order_by(News.time.desc()).offset(offset).limit(limit).all()
        
        total_pages = (total + limit - 1) // limit
        
        return {
            "data": [ {
                "id": item.id,
                "time": item.time,
                "title": item.title,
                "url": item.url,
                "description": item.description,
                "description_status": item.description_status,
                "score": item.score,
                "pair_impact": item.pair_impact,
                "direction": item.direction,
                "reason": item.reason,
                "created_at": item.created_at,
                "updated_at": item.updated_at
            } for item in items ],
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_prev": page > 1
            }
        }
    finally:
        db.close()

@router.get("/news/today")
def get_news_today():
    db = SessionLocal()
    try:
        today = date.today()
        
        items = db.query(News).filter(
            func.date(News.time) == today
        ).order_by(News.time.desc()).all()
        
        return {
            "data": [ {
                "id": item.id,
                "time": item.time,
                "title": item.title,
                "url": item.url,
                "description": item.description,
                "description_status": item.description_status,
                "score": item.score,
                "pair_impact": item.pair_impact,
                "direction": item.direction,
                "reason": item.reason,
                "created_at": item.created_at,
                "updated_at": item.updated_at
            } for item in items ]
        }
    finally:
        db.close()
