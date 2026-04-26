import os
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

BASE_URL        = "http://localhost:8000"
SYMBOLS         = [p.strip() for p in os.getenv('TRADE_PAIR', 'USDJPYm').split(',') if p.strip()]
LOT_SIZE        = float(os.getenv('LOT_SIZE', '0.01'))
FULL_HOUR_START = 8
FULL_HOUR_END   = 23

def get(path, params=None):
    return requests.get(f"{BASE_URL}{path}", params=params).json()

def post(path, payload):
    return requests.post(f"{BASE_URL}{path}", json=payload).json()

def is_full_session(hour: int) -> bool:
    return FULL_HOUR_START <= hour < FULL_HOUR_END

def is_market_open(date_str: str, hour: int) -> bool:
    dt      = datetime.strptime(date_str, "%Y-%m-%d")
    weekday = dt.weekday() 
    if weekday == 6:
        return False
    if weekday == 5 and hour >= 5:
        return False
    if weekday == 0 and hour < 5:
        return False
    return True

def get_ticket(symbol: str):
    data = get("/api/execution/position_total", {"symbol": symbol})
    if data.get("has_running") and data.get("positions"):
        return data["positions"][0]["ticket"]
    return None

def handle_buy_sell(rr: dict, symbol: str):
    result = post("/api/positions/open/market", {
        "symbol": symbol,
        "volume": LOT_SIZE,
        "type":   rr["decision"],
        "sl":     rr["sl_price"],
        "tp":     rr["tp_price"],
    })
    print(f"[{symbol}] [OPEN] {rr['decision'].upper()} | sl={rr['sl_price']} tp={rr['tp_price']} | {result}")

def handle_modify(rr: dict, symbol: str):
    ticket = get_ticket(symbol)
    if not ticket:
        print(f"[{symbol}] [MODIFY] No ticket found, skipping")
        return
    result = post("/api/positions/modify", {
        "ticket": ticket,
        "sl":     rr["sl_price"],
        "tp":     rr["tp_price"],
    })
    print(f"[{symbol}] [MODIFY] ticket={ticket} | sl={rr['sl_price']} tp={rr['tp_price']} | reason={rr['reason']} | {result}")

def handle_close(rr: dict, symbol: str):
    ticket = get_ticket(symbol)
    if not ticket:
        print(f"[{symbol}] [CLOSE] No ticket found, skipping")
        return
    result = post("/api/positions/close", {"ticket": ticket})
    print(f"[{symbol}] [CLOSE] ticket={ticket} | reason={rr['reason']} | {result}")

def run_job():
    print(f"Starting polling | symbols={SYMBOLS} | lot={LOT_SIZE}")

    while True:
        try:
            time_data   = get("/api/execution/time/now")
            date_str    = time_data.get("date", "2000-01-01")
            time_str    = time_data.get("time", "00:00:00")
            hour        = int(time_str.split(":")[0])
            session     = time_data.get("session", "-")
            full        = is_full_session(hour)
            market_open = is_market_open(date_str, hour)

            if not market_open:
                print(f"[{time_str}] Market closed (weekend), skip all executions")
                time.sleep(60)
                continue

            for symbol in SYMBOLS:
                try:
                    rr       = get("/api/execution/risk_reward", {"symbol": symbol})
                    decision = rr.get("decision", "hold")
                    valid    = rr.get("valid", False)
                    score    = rr.get("composite_score")
                    reason   = rr.get("reason")

                    print(
                        f"[{time_str}] [{symbol}] session={session} | full={full} | "
                        f"decision={decision} valid={valid} score={score} reason={reason}"
                    )

                    if decision == "hold":
                        pass

                    elif decision in ("buy", "sell"):
                        if not full:
                            print(f"[{symbol}] [SKIP] {decision.upper()} not permitted outside of hours {FULL_HOUR_START}:00-{FULL_HOUR_END}:00")
                        elif valid:
                            handle_buy_sell(rr, symbol)
                        else:
                            print(f"[{symbol}] [SKIP] {decision.upper()} valid=false | reason={reason}")

                    elif decision == "modify":
                        if valid:
                            handle_modify(rr, symbol)
                        else:
                            print(f"[{symbol}] [SKIP] MODIFY valid=false | reason={reason}")

                    elif decision == "close":
                        if valid:
                            handle_close(rr, symbol)
                        else:
                            print(f"[{symbol}] [SKIP] CLOSE valid=false | reason={reason}")
                
                except Exception as e:
                    print(f"[{symbol}] [ERROR] {e}")

        except Exception as e:
            print(f"[ERROR] {e}")

        time.sleep(3)

if __name__ == "__main__":
    run_job()