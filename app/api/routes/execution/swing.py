import math
from fastapi import APIRouter, Query
from app.databases.config import SessionLocal
from sqlalchemy import text

router = APIRouter()

TIMEFRAMES = {
    "H1":  {"table": "swings_h1",  "limit": 10},
    "M15": {"table": "swings_m15", "limit": 10},
    "M5":  {"table": "swings_m5",  "limit": 10},
    "M1":  {"table": "swings_m1",  "limit": 10},
}


def normalize_feature(values: list) -> list:
    if not values:
        return []
    vmax  = max(values)
    vmin  = min(values)
    denom = vmax - vmin
    if denom == 0:
        return [0.5] * len(values)
    return [(v - vmin) / denom for v in values]


def calc_recency_weights(n: int, signals: list) -> list:
    if n == 0:
        return []
    if n == 1:
        return [1.0]
    if len(set(signals)) == 1:
        decay = math.log(2) / (n - 1)
    else:
        decay = math.log(n) / (n - 1)
    raw   = [math.exp(-decay * i) for i in range(n)]
    total = sum(raw)
    return [w / total for w in raw]


def calc_tf_score(rows: list) -> float:
    if not rows:
        return 50.0

    signals   = [1 if r[0] == "swing_low" else -1 for r in rows]
    strengths = [float(r[1] or 0) for r in rows]
    distances = [float(r[2] or 0) for r in rows]

    str_norm = normalize_feature(strengths)

    inv_distances = [1.0 / (d + 1e-9) for d in distances]
    dist_norm     = normalize_feature(inv_distances)

    weights = calc_recency_weights(len(rows), signals)

    total_weighted = sum(
        signals[i] * str_norm[i] * dist_norm[i] * weights[i]
        for i in range(len(rows))
    )

    clamped = max(-1.0, min(1.0, total_weighted))
    return (clamped + 1.0) * 50.0


def calc_adaptive_tf_weights(tf_scores: dict) -> dict:
    values = list(tf_scores.values())
    mean   = sum(values) / len(values) if values else 50.0

    deviations = {tf: abs(tf_scores[tf] - mean) + 1e-9 for tf in tf_scores}
    total_dev  = sum(deviations.values())

    return {tf: deviations[tf] / total_dev for tf in deviations}


def calc_trend(score: float, scores_per_tf: dict) -> str:
    values = list(scores_per_tf.values())
    n      = len(values)
    mean   = sum(values) / n
    std    = math.sqrt(sum((v - mean) ** 2 for v in values) / n) if n > 1 else 0
    sem    = std / math.sqrt(n)

    if score >= mean + std:  return "strong_bullish"
    if score >= mean + sem:  return "bullish"
    if score >= mean - sem:  return "sideways"
    if score >= mean - std:  return "bearish"
    return "strong_bearish"


@router.get("/swing")
async def get_execution_swing(
    symbol: str = Query(..., description="Symbol for swing-based bias analysis")
):
    db = SessionLocal()
    try:
        tf_scores = {}

        for tf, cfg in TIMEFRAMES.items():
            rows = db.execute(text(f"""
                SELECT `type`, `strength`, `distance`, `timestamp`
                FROM {cfg["table"]}
                WHERE symbol = :symbol
                ORDER BY `timestamp` DESC
                LIMIT :lim
            """), {"symbol": symbol, "lim": cfg["limit"]}).fetchall()

            tf_scores[tf] = calc_tf_score(rows)

        tf_weights  = calc_adaptive_tf_weights(tf_scores)
        total_score = sum(tf_scores[tf] * tf_weights[tf] for tf in TIMEFRAMES)
        bias        = "bullish" if total_score > 50 else "bearish"
        trend       = calc_trend(total_score, tf_scores)

        return {
            "symbol":     symbol,
            "bias":       bias,
            "trend":      trend,
            "score":      round(total_score, 2),
            "tf_scores":  {tf: round(tf_scores[tf], 2) for tf in tf_scores},
            "tf_weights": {tf: round(tf_weights[tf], 4) for tf in tf_weights},
        }

    finally:
        db.close()