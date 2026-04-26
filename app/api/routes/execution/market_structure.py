import math
from fastapi import APIRouter, Query
from app.api.routes.market_structure import get_market_structure

router = APIRouter()

TIMEFRAMES = {
    "H1":  {"limit": 10},
    "M15": {"limit": 10},
    "M5":  {"limit": 10},
    "M1":  {"limit": 10},
}

VALUE_MAP   = {"HH": 2, "HL": 1, "LH": -1, "LL": -2}
VALUE_MAX   = max(VALUE_MAP.values())
VALUE_MIN   = min(VALUE_MAP.values())
VALUE_RANGE = VALUE_MAX - VALUE_MIN


def calc_data_consistency(values: list) -> float:
    if len(values) < 2:
        return 1.0
    mean         = sum(values) / len(values)
    variance     = sum((v - mean) ** 2 for v in values) / len(values)
    max_variance = (VALUE_RANGE / 2) ** 2
    return max(0.0, 1.0 - (variance / max_variance))


def calc_exp_weights(values: list) -> list:
    n = len(values)
    if n == 0:
        return []
    if n == 1:
        return [1.0]
    consistency = calc_data_consistency(values)
    decay_min   = math.log(2) / (n - 1)
    decay_max   = math.log(n) / (n - 1)
    decay       = decay_min + (1 - consistency) * (decay_max - decay_min)
    raw         = [math.exp(decay * i) for i in range(n)]
    total       = sum(raw)
    return [w / total for w in raw]


def structure_score(items: list) -> tuple:
    if not items:
        return 0, []
    values  = [VALUE_MAP.get(item.get("structure_type"), 0) for item in items]
    weights = calc_exp_weights(values)
    score   = sum(v * w for v, w in zip(values, weights))
    return score, values


def normalize(score: float, values: list) -> float:
    if not values:
        return 50.0
    weights   = calc_exp_weights(values)
    max_score = sum(VALUE_MAX * w for w in weights)
    min_score = sum(VALUE_MIN * w for w in weights)
    denom     = max_score - min_score
    if denom == 0:
        return 50.0
    normalized = (score - min_score) / denom
    return max(0.0, min(100.0, normalized * 100))


def get_tf_score(data: dict) -> float:
    if not data or not data.get("data"):
        return 50.0
    raw, values = structure_score(data["data"])
    return normalize(raw, values)


def calc_adaptive_tf_weights(tf_scores: dict) -> dict:
    values = list(tf_scores.values())
    mean   = sum(values) / len(values) if values else 50.0

    deviations = {tf: abs(tf_scores[tf] - mean) + 1e-9 for tf in tf_scores}
    total_dev  = sum(deviations.values())

    return {tf: deviations[tf] / total_dev for tf in deviations}


def calc_trend(score: float, scores_per_tf: dict) -> str:
    # values = list(scores_per_tf.values())
    # n      = len(values)
    # mean   = sum(values) / n
    # std    = math.sqrt(sum((v - mean) ** 2 for v in values) / n) if n > 1 else 0
    # sem    = std / math.sqrt(n)

    # upper_strong = mean + std
    # upper_weak   = mean + sem
    # lower_weak   = mean - sem
    # lower_strong = mean - std

    if score >= 70:
        trend = "strong_bullish"
    elif score >= 55:
        trend = "bullish"
    elif score >= 45:
        trend = "sideways"
    elif score >= 30:
        trend = "bearish"
    else:
        trend = "strong_bearish"
    return trend


@router.get("/market_structure")
async def get_execution_market_structure(
    symbol: str = Query(..., description="Symbol for market structure analysis")
):
    raw_data = {
        tf: get_market_structure(tf, symbol, page=1, limit=cfg["limit"])
        for tf, cfg in TIMEFRAMES.items()
    }

    tf_scores   = {tf: get_tf_score(raw_data[tf]) for tf in TIMEFRAMES}
    tf_weights  = calc_adaptive_tf_weights(tf_scores)
    total_score = sum(tf_scores[tf] * tf_weights[tf] for tf in tf_scores)
    trend       = calc_trend(total_score, tf_scores)

    return {
        "symbol":     symbol,
        "trend":      trend,
        "score":      round(total_score, 2),
        "tf_scores":  {tf: round(tf_scores[tf], 2) for tf in tf_scores},
        "tf_weights": {tf: round(tf_weights[tf], 4) for tf in tf_weights},
    }