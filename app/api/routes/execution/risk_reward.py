import math
import logging
from fastapi import APIRouter, Query
from datetime import datetime
import pytz
import httpx
import asyncio
from app.databases.config import SessionLocal
from sqlalchemy import text

router = APIRouter()
JAKARTA_TZ = pytz.timezone("Asia/Jakarta")
BASE_URL = "http://localhost:8000/api/execution"
logger = logging.getLogger(__name__)

SESSION_MINUTES = {"Asia": 480, "London": 300, "New York": 660}
TOTAL_MINUTES = sum(SESSION_MINUTES.values())


def get_session(hour: int):
    if 6 <= hour < 14:
        return "Asia", SESSION_MINUTES["Asia"] / TOTAL_MINUTES
    if 14 <= hour < 19:
        return "London", SESSION_MINUTES["London"] / TOTAL_MINUTES
    return "New York", SESSION_MINUTES["New York"] / TOTAL_MINUTES


def build_response(symbol, session, session_factor, running_positions, **overrides):
    base = {
        "symbol": symbol,
        "valid": False,
        "decision": "hold",
        "reason": None,
        "composite_score": None,
        "direction": None,
        "session": session,
        "session_factor": round(session_factor, 4),
        "current_price": None,
        "entry_price": None,
        "tp_price": None,
        "sl_price": None,
        "ratio": None,
        "running_positions": running_positions,
    }
    base.update(overrides)
    return base


async def safe_fetch(client, url, params):
    try:
        r = await client.get(url, params=params)
        r.raise_for_status()
        return r.json()
    except:
        return {}


def calc_composite(ms, swing, nc):
    base = (ms + swing) / 2
    nc_w = abs(nc) / (abs(nc) + base + 1e-9)
    return max(0.0, min(100.0, base + nc * nc_w))


def calc_news_calendar_score(news, cal):
    n = news.get("average_score", 0)
    hi = cal.get("high_impact_valid", False)
    mi = cal.get("medium_impact_valid", False)
    penalty = -20 if hi else (-10 if mi else 0)
    return float(n + penalty)


def rr_multiplier(score):
    if score >= 80:
        return 3.0
    if score >= 65:
        return 2.5
    return 2.0


def simple_entry(db, symbol, current_price, composite_score):
    direction = "buy" if composite_score >= 50 else "sell"

    rows = db.execute(text("""
        SELECT type, price FROM swings_m1
        WHERE symbol = :symbol
        ORDER BY timestamp DESC LIMIT 10
    """), {"symbol": symbol}).fetchall()

    if not rows:
        return None

    swings = [{"type": r[0], "price": float(r[1])} for r in rows[::-1]]

    low = next((s for s in reversed(swings) if s["type"] == "swing_low"), None)
    high = next((s for s in reversed(swings) if s["type"] == "swing_high"), None)

    if not low or not high:
        return None

    entry = current_price
    buffer = abs(high["price"] - low["price"]) * 0.2
    buffer = max(buffer, 0.12)

    if direction == "buy":
        sl = entry - buffer
        tp = entry + rr_multiplier(composite_score) * buffer
    else:
        sl = entry + buffer
        tp = entry - rr_multiplier(composite_score) * buffer

    risk = abs(entry - sl)
    rr = abs(tp - entry) / risk if risk > 0 else 0

    if rr < 2:
        return None

    return {
        "direction": direction,
        "entry_price": entry,
        "sl_price": sl,
        "tp_price": tp,
        "ratio": f"1:{rr:.1f}"
    }


@router.get("/risk_reward")
async def get_execution_risk_reward(symbol: str = Query(...)):
    db = SessionLocal()
    try:
        now = datetime.now(JAKARTA_TZ)
        session, session_factor = get_session(now.hour)

        pos = db.execute(text("""
            SELECT COUNT(*) FROM positions
            WHERE symbol = :symbol AND is_running = 1
        """), {"symbol": symbol}).fetchone()

        running_positions = pos[0] if pos else 0

        price = db.execute(text("""
            SELECT close FROM ohlc_m1
            WHERE symbol = :symbol
            ORDER BY time DESC LIMIT 1
        """), {"symbol": symbol}).fetchone()

        if not price:
            return build_response(symbol, session, session_factor, running_positions, reason="no_price")

        current_price = float(price[0])

        if running_positions > 0:
            async with httpx.AsyncClient() as client:
                speed, news, cal = await asyncio.gather(
                    safe_fetch(client, f"{BASE_URL}/candle_speed", {"symbol": symbol}),
                    safe_fetch(client, f"{BASE_URL}/news", {"symbol": symbol}),
                    safe_fetch(client, f"{BASE_URL}/calendar", {"symbol": symbol}),
                )

            speed_score = float(speed.get("score", 50))
            direction = speed.get("direction", "neutral")

            nc = calc_news_calendar_score(news, cal)

            pos_detail = db.execute(text("""
                SELECT type, price, sl, tp FROM positions
                WHERE symbol = :symbol AND is_running = 1
                ORDER BY time DESC LIMIT 1
            """), {"symbol": symbol}).fetchone()

            if not pos_detail:
                return build_response(symbol, session, session_factor, running_positions, reason="no_position_detail")

            pos_type = pos_detail[0]
            pos_entry = float(pos_detail[1])
            pos_sl = float(pos_detail[2])
            pos_tp = float(pos_detail[3])

            is_profit = (current_price > pos_entry) if pos_type == "buy" else (current_price < pos_entry)
            match = (direction == "bullish" and pos_type == "buy") or (direction == "bearish" and pos_type == "sell")

            if speed.get("speed") == "spike" and not match:
                return build_response(
                    symbol, session, session_factor, running_positions,
                    valid=True,
                    decision="close",
                    reason="reverse_spike",
                    current_price=round(current_price, 5),
                    entry_price=pos_entry,
                    sl_price=pos_sl,
                    tp_price=pos_tp,
                )

            return build_response(
                symbol, session, session_factor, running_positions,
                valid=False,
                decision="hold",
                reason="monitoring",
                current_price=round(current_price, 5),
                entry_price=pos_entry,
                sl_price=pos_sl,
                tp_price=pos_tp,
            )

        async with httpx.AsyncClient() as client:
            ms, swing, news, cal = await asyncio.gather(
                safe_fetch(client, f"{BASE_URL}/market_structure", {"symbol": symbol}),
                safe_fetch(client, f"{BASE_URL}/swing", {"symbol": symbol}),
                safe_fetch(client, f"{BASE_URL}/news", {"symbol": symbol}),
                safe_fetch(client, f"{BASE_URL}/calendar", {"symbol": symbol}),
            )

        ms_score = float(ms.get("score", 50))
        swing_score = float(swing.get("score", 50))
        nc = calc_news_calendar_score(news, cal)

        composite = calc_composite(ms_score, swing_score, nc)
        composite = max(0.0, min(100.0, composite * session_factor + 50 * (1 - session_factor)))

        entry_data = simple_entry(db, symbol, current_price, composite)

        if not entry_data:
            return build_response(symbol, session, session_factor, running_positions, reason="filtered")

        return build_response(
            symbol,
            session,
            session_factor,
            running_positions,
            valid=True,
            decision=entry_data["direction"],
            composite_score=round(composite, 2),
            current_price=round(current_price, 5),
            entry_price=round(entry_data["entry_price"], 5),
            sl_price=round(entry_data["sl_price"], 5),
            tp_price=round(entry_data["tp_price"], 5),
            ratio=entry_data["ratio"],
        )

    finally:
        db.close()