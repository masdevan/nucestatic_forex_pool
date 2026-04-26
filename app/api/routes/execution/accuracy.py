import math
from fastapi import APIRouter, Query

router = APIRouter()

def calc_exp_weights(n: int) -> list:
    if n == 0:
        return []
    decay = math.log(20) / max(n - 1, 1)
    raw   = [math.exp(decay * i) for i in range(n)]
    total = sum(raw)
    return [w / total for w in raw]

def calc_avg_atr(history: list) -> float:
    atrs = [float(r[4] or 0) for r in history if r[7] == 1 and float(r[4] or 0) > 0]
    return sum(atrs) / len(atrs) if atrs else 0

def calc_median_body(history: list) -> float:
    bodies = sorted(
        abs(float(r[3] or 0) - float(r[0] or 0))
        for r in history if r[7] == 1
    )
    if not bodies:
        return 0
    mid = len(bodies) // 2
    return (bodies[mid - 1] + bodies[mid]) / 2 if len(bodies) % 2 == 0 else bodies[mid]

def calc_atr_consistency(history: list) -> float:
    atrs = [float(r[4] or 0) for r in history if r[7] == 1 and float(r[4] or 0) > 0]
    if len(atrs) < 2:
        return 1.0
    mean = sum(atrs) / len(atrs)
    std  = math.sqrt(sum((a - mean) ** 2 for a in atrs) / len(atrs))
    cv   = std / mean if mean > 0 else 1.0
    return max(0.0, 1.0 - cv)

def detect_setup_type(history: list, type: str) -> str:
    if not history:
        return "unknown"
    against = sum(
        1 for r in history
        if (type == "sell" and float(r[3] or 0) > float(r[0] or 0)) or
           (type == "buy"  and float(r[3] or 0) < float(r[0] or 0))
    )
    ratio = against / len(history)
    if ratio >= 0.6:
        return "reversal"
    elif ratio <= 0.3:
        return "continuation"
    return "mixed"

def calc_candle_score(row, type: str, avg_atr: float, median_body: float, setup: str) -> float:
    open_, high, low, close, atr, sweep_high, sweep_low, is_done = row

    open_   = float(open_   or 0)
    close   = float(close   or 0)
    atr     = float(atr     or 0)
    avg_atr = float(avg_atr or 0)

    if type == "buy":
        base = 1 if close > open_ else 0
        if setup == "reversal":
            sweep = 1 if sweep_low == 1 else 0
        else:
            body  = abs(close - open_)
            sweep = 0.5 if median_body > 0 and body >= median_body else 0
    else:
        base = 1 if close < open_ else 0
        if setup == "reversal":
            sweep = 1 if sweep_high == 1 else 0
        else:
            body  = abs(close - open_)
            sweep = 0.5 if median_body > 0 and body >= median_body else 0

    atr_score = min(atr / avg_atr, 1) if avg_atr > 0 else 0

    score  = base
    score += atr_score * 0.3
    score += sweep     * 0.2

    return min(score, 1)

def calc_weighted_history_score(history: list, type: str, avg_atr: float, median_body: float, setup: str) -> float:
    valid   = [r for r in history if r[7] == 1]
    if not valid:
        return 0
    weights = calc_exp_weights(len(valid))
    return sum(
        calc_candle_score(r, type, avg_atr, median_body, setup) * w
        for r, w in zip(valid, weights)
    )

def calc_streak(history: list, type: str) -> int:
    streak = 0
    for r in reversed(history):
        open_ = float(r[0] or 0)
        close = float(r[3] or 0)
        if   type == "buy"  and close > open_: streak += 1
        elif type == "sell" and close < open_: streak += 1
        else: break
    return streak

def compute_block(block: list, type: str) -> float:
    last    = block[-1]
    history = block[:-1]

    valid_history = [r for r in history if r[7] == 1]
    if not valid_history:
        return 0

    avg_atr     = calc_avg_atr(valid_history)
    median_body = calc_median_body(valid_history)
    consistency = calc_atr_consistency(valid_history)
    setup       = detect_setup_type(valid_history, type)

    history_score = calc_weighted_history_score(valid_history, type, avg_atr, median_body, setup)
    last_score    = calc_candle_score(last, type, avg_atr, median_body, setup)

    score = history_score * 0.8 + last_score * 0.2

    avg_price = float(last[3] or 1)
    if avg_price > 0 and avg_atr > 0:
        atr_ratio = avg_atr / avg_price
        if atr_ratio < 0.00003:
            score *= max(0.3, atr_ratio / 0.00003)

    streak       = calc_streak(valid_history, type)
    streak_ratio = streak / len(valid_history) if valid_history else 0
    if streak_ratio >= 0.8:
        score *= 0.6
    elif streak_ratio >= 0.6:
        score *= 0.8

    last_close = float(last[3] or 0)
    last_open  = float(last[0] or 0)
    last_high  = float(last[1] or 0)
    last_low   = float(last[2] or 0)
    prev_high  = float(history[-1][1] or 0)
    prev_low   = float(history[-1][2] or 0)

    if setup == "reversal":
        if type == "buy"  and last_close <= prev_high:
            score *= 1 - consistency * 0.3
        if type == "sell" and last_close >= prev_low:
            score *= 1 - consistency * 0.3

        dist       = abs(last_close - last_low) if type == "buy" else abs(last_close - last_high)
        dist_ratio = dist / avg_atr if avg_atr > 0 else 0
        if dist_ratio > 1.5:
            score *= max(0.7, 1 - (dist_ratio - 1.5) * 0.1)

    elif setup == "continuation":
        body       = abs(last_close - last_open)
        body_ratio = body / median_body if median_body > 0 else 0
        if body_ratio >= 1.0:
            bonus  = min(1 + (body_ratio - 1.0) * 0.15 * consistency, 1.2)
            score *= bonus

        if type == "buy"  and last_close < last_open:
            score *= 1 - consistency * 0.25
        if type == "sell" and last_close > last_open:
            score *= 1 - consistency * 0.25

    return min(score, 1)

@router.get("/accuracy")
async def get_accuracy(
    symbol: str = Query(...),
    type:   str = Query(..., description="buy or sell")
):
    from app.databases.config import SessionLocal
    from sqlalchemy import text

    db = SessionLocal()
    try:
        m1_rows = db.execute(text("""
            SELECT open, high, low, close, atr, sweep_high, sweep_low, is_done
            FROM ohlc_m1
            WHERE symbol = :symbol
            ORDER BY time DESC
            LIMIT 12
        """), {"symbol": symbol}).fetchall()

        score        = 0.0
        prev_score   = 0.0
        entry_signal = False
        setup_type   = "unknown"
        consistency  = 0.0

        if len(m1_rows) == 12:
            data = list(reversed(m1_rows))
            t    = type.lower()

            prev_block = data[:6]
            curr_block = data[6:]

            prev_score = compute_block(prev_block, t) * 100
            score      = compute_block(curr_block, t) * 100

            valid_curr  = [r for r in curr_block[:-1] if r[7] == 1]
            setup_type  = detect_setup_type(valid_curr, t)
            consistency = round(calc_atr_consistency(valid_curr), 3)

            rel_delta    = (score - prev_score) / max(prev_score, 0.01)
            entry_signal = (score >= 50 and rel_delta >= 0.10) or (score >= 65)

        return {
            "symbol":          symbol,
            "type":            type.lower(),
            "setup":           setup_type,
            "consistency":     consistency,
            "m1_candle_total": len(m1_rows),
            "score":           round(score,             2),
            "prev_score":      round(prev_score,        2),
            "delta":           round(score - prev_score, 2),
            "entry":           entry_signal,
        }

    finally:
        db.close()