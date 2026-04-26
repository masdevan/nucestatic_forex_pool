from fastapi import APIRouter
from datetime import datetime
import pytz

router = APIRouter()

JAKARTA_TZ = pytz.timezone('Asia/Jakarta')

@router.get("/time/now")
async def get_current_time():
    now = datetime.now(JAKARTA_TZ)
    hour = now.hour

    if 6 <= hour < 14:
        session_id = 1
        session = 'Asia'
    elif 14 <= hour < 19:
        session_id = 2
        session = 'London'
    else:
        session_id = 3
        session = 'New York'

    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "session": session,
        "session_id": session_id
    }
