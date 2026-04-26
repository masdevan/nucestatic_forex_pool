from fastapi import APIRouter, Query
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.databases.config import SessionLocal
from app.databases.models.calendar_model import Calendar

router = APIRouter()

LOCAL_TZ = ZoneInfo("Asia/Jakarta")

def get_today_range():
    now = datetime.now(LOCAL_TZ)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start, end

@router.get("/calendar")
async def get_execution_calendar(symbol: str = Query(...)):
    db = SessionLocal()

    try:
        currency1 = symbol[:3].upper()
        currency2 = symbol[3:6].upper()

        start, end = get_today_range()
        now = datetime.now(LOCAL_TZ)

        items = db.query(Calendar).filter(
            Calendar.time >= start,
            Calendar.time <= end,
            Calendar.currency.in_([currency1, currency2]),
            Calendar.impact.in_(['high', 'medium'])
        ).order_by(Calendar.time.asc()).all()

        high_impact = 0
        medium_impact = 0

        high_impact_valid = False
        medium_impact_valid = False

        filtered = []

        for item in items:
            impact = str(item.impact).lower()

            event_time = item.time
            if event_time.tzinfo is None:
                event_time = event_time.replace(tzinfo=LOCAL_TZ)

            if impact == "high":
                high_impact += 1
                start_window = event_time - timedelta(minutes=15)
                end_window = event_time + timedelta(minutes=30)
            else:
                medium_impact += 1
                start_window = event_time - timedelta(minutes=10)
                end_window = event_time + timedelta(minutes=15)

            in_window = start_window <= now <= end_window

            if in_window:
                filtered.append({
                    "id": item.id,
                    "time": item.time,
                    "currency": item.currency,
                    "event": item.event,
                    "impact": item.impact,
                    "actual": item.actual,
                    "forecast": item.forecast,
                    "previous": item.previous
                })

                if impact == "high":
                    high_impact_valid = True
                elif impact == "medium":
                    medium_impact_valid = True

        return {
            "symbol": symbol,
            "now": now.isoformat(),
            "timezone": "Asia/Jakarta",
            "currencies": [currency1, currency2],
            "high_impact": high_impact,
            "medium_impact": medium_impact,
            "total_events": len(items),
            "high_impact_valid": high_impact_valid,
            "medium_impact_valid": medium_impact_valid,
        }

    finally:
        db.close()