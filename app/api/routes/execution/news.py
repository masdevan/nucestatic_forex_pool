from fastapi import APIRouter, Query
from datetime import date
from app.databases.config import SessionLocal
from app.databases.models.news_model import News
from sqlalchemy import func, or_

router = APIRouter()

@router.get("/news")
async def get_execution_news(
    symbol: str = Query(..., description="Symbol to filter news impact")
):
    db = SessionLocal()
    try:
        currency1 = symbol[:3].upper()
        currency2 = symbol[3:6].upper()

        today = date.today()

        items = db.query(News).filter(
            func.date(News.time) == today,
            or_(
                News.pair_impact.contains(currency1),
                News.pair_impact.contains(currency2)
            )
        ).order_by(News.time.desc()).all()

        total_score = 0
        bullish_count = 0
        bearish_count = 0
        neutral_count = 0

        currency_scores = {
            currency1: 0.0,
            currency2: 0.0
        }

        for item in items:
            score = float(item.score or 0)
            total_score += score

            direction_raw = (item.direction or "")
            direction = direction_raw.strip().upper()

            if "BULLISH" in direction:
                bullish_count += 1
            elif "BEARISH" in direction:
                bearish_count += 1
            else:
                neutral_count += 1

            parts = direction.split()

            if len(parts) >= 2:
                sentiment = parts[0].strip()
                target_currency = parts[1].strip()[:3]

                if target_currency in currency_scores:
                    if sentiment == "BULLISH":
                        currency_scores[target_currency] += score
                    elif sentiment == "BEARISH":
                        currency_scores[target_currency] -= score

            if item.pair_impact:
                clean_symbol = symbol.replace("m", "")
                if clean_symbol in item.pair_impact:
                    for currency in [currency1, currency2]:
                        if currency in direction:
                            if "BULLISH" in direction:
                                currency_scores[currency] += score * 0.2
                            elif "BEARISH" in direction:
                                currency_scores[currency] -= score * 0.2

        avg_score = total_score / len(items) if items else 0

        def get_bias(score):
            if score > 100:
                return "strong_bullish"
            elif score > 40:
                return "bullish"
            elif score < -100:
                return "strong_bearish"
            elif score < -40:
                return "bearish"
            else:
                return "neutral"

        currency_bias = {
            currency1: get_bias(currency_scores[currency1]),
            currency2: get_bias(currency_scores[currency2])
        }

        return {
            "symbol": symbol,
            "currencies": [currency1, currency2],
            "average_score": round(avg_score, 2),
            "bullish_count": bullish_count,
            "bearish_count": bearish_count,
            "neutral_count": neutral_count,
            "total_news": len(items),
            "currency_scores": currency_scores,
            "currency_bias": currency_bias
        }

    finally:
        db.close()