from fastapi import APIRouter, Query
from app.databases.config import SessionLocal
from sqlalchemy import text
from decimal import Decimal

router = APIRouter()

DIRECTION_WEIGHT = {
    "bullish_spike":  2,
    "bullish":        1,
    "neutral":        0,
    "bearish":       -1,
    "bearish_spike": -2,
}


def to_dec(val):
    return Decimal(str(val)) if val is not None else Decimal("0")


def fetch_candles(db, table, symbol, limit):
    rows = db.execute(text(f"""
        SELECT open, high, low, close, tick_volume, atr,
               sweep_high, sweep_low, sweep_strength
        FROM {table}
        WHERE symbol = :symbol
          AND is_done = 1
        ORDER BY time DESC
        LIMIT {limit}
    """), {"symbol": symbol}).fetchall()
    return list(reversed(rows))


def get_range(c):
    return to_dec(c[1]) - to_dec(c[2])


def get_body(c):
    return abs(to_dec(c[3]) - to_dec(c[0]))


def detect_range_expansion(last, base):
    atrs = [to_dec(c[5]) for c in base if to_dec(c[5]) > 0]
    if not atrs:
        return "unknown", 1, 50

    avg_atr = sum(atrs) / len(atrs)
    last_range = get_range(last)
    ratio = last_range / avg_atr if avg_atr > 0 else 0

    if ratio >= 3:
        return "explosive", float(ratio), 95
    elif ratio >= 2:
        return "strong", float(ratio), 85
    elif ratio >= 1.2:
        return "expanded", float(ratio), 70
    else:
        return "normal", float(ratio), 50


def detect_sudden_jump(last, prev):
    last_range = get_range(last)
    prev_range = get_range(prev)

    if prev_range == 0:
        return False, 1, 50

    jump = last_range / prev_range

    if jump >= 2.5:
        return True, float(jump), 90
    elif jump >= 1.5:
        return False, float(jump), 65
    else:
        return False, float(jump), 50


def detect_volume_spike(last, base):
    vols = [to_dec(c[4]) for c in base if to_dec(c[4]) > 0]
    if not vols:
        return "normal", 1, 50

    avg = sum(vols) / len(vols)
    last_vol = to_dec(last[4])
    ratio = last_vol / avg if avg > 0 else 0

    if ratio >= 3:
        return "explosive", float(ratio), 90
    elif ratio >= 2:
        return "high", float(ratio), 80
    elif ratio >= 1.3:
        return "above_avg", float(ratio), 65
    else:
        return "normal", float(ratio), 50


def detect_sweep(last):
    strength = to_dec(last[8])
    has_sweep = to_dec(last[6]) > 0 or to_dec(last[7]) > 0

    if not has_sweep:
        return "none", 0, 45

    if strength >= Decimal("0.20"):
        return "strong", float(strength), 90
    elif strength >= Decimal("0.10"):
        return "medium", float(strength), 75
    else:
        return "weak", float(strength), 60


def detect_direction(last, prev):
    last_body = get_body(last)
    prev_body = get_body(prev)

    if prev_body == 0:
        return "neutral", 0

    ratio = last_body / prev_body

    if ratio >= 2:
        if to_dec(last[3]) > to_dec(last[0]):
            return "bullish_spike", float(ratio)
        else:
            return "bearish_spike", float(ratio)

    if to_dec(last[3]) > to_dec(last[0]):
        return "bullish", float(ratio)
    elif to_dec(last[3]) < to_dec(last[0]):
        return "bearish", float(ratio)

    return "neutral", float(ratio)


def aggregate_direction(weighted_score: float) -> str:
    if weighted_score >= 0.8:
        return "bullish"
    elif weighted_score <= -0.8:
        return "bearish"
    else:
        return "neutral"


def classify_candle(last, prev, base):
    range_type, range_ratio, s_range = detect_range_expansion(last, base)
    sudden, jump_ratio, s_jump = detect_sudden_jump(last, prev)
    vol_type, vol_ratio, s_vol = detect_volume_spike(last, base)
    sweep_type, sweep_strength, s_sweep = detect_sweep(last)
    direction, body_ratio = detect_direction(last, prev)

    score = (
        Decimal(s_range) * Decimal("0.4") +
        Decimal(s_vol) * Decimal("0.3") +
        Decimal(s_sweep) * Decimal("0.2") +
        Decimal(s_jump) * Decimal("0.1")
    )

    score = float(score.quantize(Decimal("0.01")))

    if (range_type in ["strong", "explosive"] and sudden):
        return "true_spike", score, {"sweep": sweep_strength}, direction

    if (sweep_type in ["strong", "medium"] and range_type == "normal"):
        return "liquidity_grab", score, {"sweep": sweep_strength}, direction

    if (vol_type in ["high", "explosive"] and range_type == "normal"):
        return "volume_push", score, {"sweep": sweep_strength}, direction

    if range_type in ["expanded"] and direction in ["bullish", "bearish"]:
        return "trend_move", score, {"sweep": sweep_strength}, direction

    return "normal", score, {"sweep": sweep_strength}, direction


@router.get("/candle_speed")
async def detect_candle(symbol: str = Query(...)):
    db = SessionLocal()

    try:
        results = {}
        weighted = Decimal("0")
        weighted_dir = Decimal("0")

        weights = {
            "M1": Decimal("0.6"),
            "M5": Decimal("0.4")
        }

        for tf in ["M1", "M5"]:
            table = f"ohlc_{tf.lower()}"
            candles = fetch_candles(db, table, symbol, 50)

            if len(candles) < 10:
                results[tf] = {"error": "not_enough_data"}
                continue

            last = candles[-1]
            prev = candles[-2]
            base = candles[:-1]

            classification, score, detail, direction = classify_candle(last, prev, base)

            weighted += Decimal(score) * weights[tf]
            weighted_dir += Decimal(DIRECTION_WEIGHT.get(direction, 0)) * weights[tf]

            results[tf] = {
                "type": classification,
                "score": score,
                "direction": direction,
                "detail": detail
            }

        avg_score = float(weighted.quantize(Decimal("0.01")))
        final_direction = aggregate_direction(float(weighted_dir))

        if avg_score >= 85:
            speed = "spike"
        elif avg_score >= 70:
            speed = "fast"
        elif avg_score >= 55:
            speed = "normal"
        else:
            speed = "slow"

        return {
            "symbol": symbol,
            "speed": speed,
            "score": avg_score,
            "direction": final_direction,
        }

    finally:
        db.close()