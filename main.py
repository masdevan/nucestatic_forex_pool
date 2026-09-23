import os
import re
import time
from datetime import datetime
from pathlib import Path
import uvicorn
import httpx
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from starlette.responses import Response, FileResponse
from sqlalchemy import text
from pydantic import BaseModel
from typing import Any
from app.api.models.ohlc_model import CandleIngest
# from app.api.models.configs.mt5_config import init_mt5, shutdown_mt5, get_terminal_info

load_dotenv()

PORT = int(os.getenv("PORT", "8765"))
TYPE = os.getenv("TYPE", "static").strip().lower()
if TYPE not in ("static", "dynamic"):
    TYPE = "static"
MIN_START_DATE = os.getenv("MIN_START_DATE", "").strip()
try:
    datetime.strptime(MIN_START_DATE, "%Y-%m-%d")
except ValueError:
    MIN_START_DATE = ""
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]
APP_NAME = os.getenv("NAME", "FOREXPOOL").strip() or "FOREXPOOL"

app = FastAPI(
    title=APP_NAME,
    description="API market data",
    version="1.0.0"
)

if CORS_ORIGINS:
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

TIMEFRAMES = {"m1", "m5", "m15", "m30", "h1", "h4", "d1", "w1", "mn1"}

_TABLE_CACHE = {}
_TABLE_CACHE_TTL = 60

def table_exists(db, tbl):
    now = time.time()
    cached = _TABLE_CACHE.get(tbl)
    if cached is not None and now - cached[0] < _TABLE_CACHE_TTL:
        return cached[1]
    from sqlalchemy import text as sql_text
    check = db.execute(sql_text(
        "SELECT COUNT(*) FROM information_schema.tables "
        "WHERE table_schema = DATABASE() AND table_name = :tbl"
    ), {"tbl": tbl}).scalar()
    exists = bool(check)
    _TABLE_CACHE[tbl] = (now, exists)
    return exists

@app.get("/api/health")
async def health_check():
    # terminal = get_terminal_info()
    return {
        "status": "healthy",
        "type": TYPE,
        "min_start_date": MIN_START_DATE or None,
        # "mt5_connected": terminal is not None
    }

@app.get("/api/symbols")
def symbols(search: str = None, limit: int = Query(50, ge=1, le=1000), page: int = Query(1, ge=1)):
    from math import ceil
    from app.databases.config import SessionLocal
    db = SessionLocal()
    try:
        where = ""
        params = {}
        if search:
            where = " WHERE name LIKE :q"
            params["q"] = f"%{search}%"
        rows = db.execute(text(
            f"SELECT server, name FROM symbols{where} ORDER BY name ASC LIMIT {limit} OFFSET {(page - 1) * limit}"
        ), params).fetchall()
        total = db.execute(text(
            f"SELECT COUNT(*) FROM symbols{where}"
        ), params).scalar()
        total_pages = ceil(total / limit) if total > 0 else 1
        return {
            "symbols": [{"server": r[0], "name": r[1]} for r in rows],
            "total": total,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
                "has_next": page * limit < total,
                "has_prev": page > 1
            }
        }
    finally:
        db.close()

@app.get("/api/symbols/{symbol}/range")
def symbol_range(symbol: str):
    from app.databases.config import SessionLocal
    db = SessionLocal()
    try:
        rows = db.execute(text(
            "SELECT timeframe, first_ts, last_ts, count FROM symbol_ranges WHERE symbol = :sym ORDER BY FIELD(timeframe, 'M1','M5','M15','M30','H1','H4','D1','W1','MN1')"
        ), {"sym": symbol}).fetchall()
        return {"symbol": symbol, "ranges": [
            {"timeframe": r[0], "first": r[1].strftime("%Y-%m-%d %H:%M:%S") if r[1] else None,
             "last": r[2].strftime("%Y-%m-%d %H:%M:%S") if r[2] else None, "count": r[3]}
            for r in rows
        ]}
    finally:
        db.close()

@app.get("/api/ohlc/{symbol}")
def symbol_ohlc(
    symbol: str,
    timeframe: str = Query("m1"),
    start_date: str = Query(None),
    end_date: str = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    page: int = Query(1, ge=1),
    cursor: int = Query(None),
    before: int = Query(None)
):
    from app.databases.config import SessionLocal
    from sqlalchemy import text as sql_text
    from datetime import datetime

    tf_lower = timeframe.lower()
    if not re.match(r"^[A-Za-z0-9_]+$", symbol) or tf_lower not in TIMEFRAMES:
        return {"symbol": symbol, "timeframe": timeframe, "data": [], "has_next": False, "next_cursor": None}

    tbl = f"ohlc_{symbol.lower()}_{tf_lower}"
    db = SessionLocal()
    try:
        if not table_exists(db, tbl):
            return {"symbol": symbol, "timeframe": timeframe, "data": [], "has_next": False, "next_cursor": None}

        where_clauses = ["symbol = :sym"]
        params = {"sym": symbol}

        if before is not None:
            where_clauses.append("time < :before")
            params["before"] = before
        elif cursor is not None:
            where_clauses.append("time > :cursor")
            params["cursor"] = cursor

        if start_date:
            for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    dt = datetime.strptime(start_date, fmt)
                    where_clauses.append("time >= :start")
                    params["start"] = int(dt.timestamp())
                    break
                except ValueError:
                    continue
        if end_date:
            for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    dt = datetime.strptime(end_date, fmt)
                    if fmt == "%Y-%m-%d":
                        dt = dt.replace(hour=23, minute=59)
                    where_clauses.append("time <= :end")
                    params["end"] = int(dt.timestamp())
                    break
                except ValueError:
                    continue

        where_sql = " AND ".join(where_clauses)
        fetch = limit + 1

        if before is not None:
            rows = db.execute(sql_text(
                f"SELECT symbol, open, high, low, close, time FROM `{tbl}` "
                f"WHERE {where_sql} ORDER BY time DESC LIMIT {fetch}"
            ), params).fetchall()
            has_next = len(rows) > limit
            rows = list(reversed(rows[:limit]))
        elif cursor is not None:
            rows = db.execute(sql_text(
                f"SELECT symbol, open, high, low, close, time FROM `{tbl}` "
                f"WHERE {where_sql} ORDER BY time ASC LIMIT {fetch}"
            ), params).fetchall()
        else:
            skip = (page - 1) * limit
            anchor = None
            try:
                anchor = db.execute(sql_text(
                    "SELECT start_time FROM ohlc_page_anchor "
                    "WHERE symbol = :s AND timeframe = :tf AND k = :k LIMIT 1"
                ), {"s": symbol, "tf": tf_lower.upper(), "k": skip // 1000}).scalar()
            except Exception:
                anchor = None
            if anchor is not None and not start_date and not end_date:
                aparams = dict(params)
                aparams["anchor"] = anchor
                anchor_where = where_sql + " AND time >= :anchor"
                rows = db.execute(sql_text(
                    f"SELECT o.symbol, o.open, o.high, o.low, o.close, o.time "
                    f"FROM `{tbl}` o JOIN (SELECT id FROM `{tbl}` WHERE {anchor_where} "
                    f"ORDER BY time ASC LIMIT {fetch} OFFSET {skip % 1000}) t ON o.id = t.id "
                    f"ORDER BY o.time ASC"
                ), aparams).fetchall()
            else:
                rows = db.execute(sql_text(
                    f"SELECT o.symbol, o.open, o.high, o.low, o.close, o.time "
                    f"FROM `{tbl}` o JOIN (SELECT id FROM `{tbl}` WHERE {where_sql} "
                    f"ORDER BY time ASC LIMIT {fetch} OFFSET {(page - 1) * limit}) t ON o.id = t.id "
                    f"ORDER BY o.time ASC"
                ), params).fetchall()

        def fmt(v):
            if isinstance(v, (int, float)):
                return datetime.fromtimestamp(v).strftime("%Y-%m-%d %H:%M")
            if hasattr(v, 'strftime'):
                return v.strftime("%Y-%m-%d %H:%M")
            return str(v) if v else None

        if before is None:
            has_next = len(rows) > limit
        data = []
        for r in rows[:limit]:
            data.append({
                "symbol": r[0],
                "open": float(r[1]) if r[1] else None,
                "high": float(r[2]) if r[2] else None,
                "low": float(r[3]) if r[3] else None,
                "close": float(r[4]) if r[4] else None,
                "time": fmt(r[5])
            })

        next_cursor = None
        if data:
            last = rows[0][5] if before is not None else rows[len(data) - 1][5]
            next_cursor = int(last) if isinstance(last, (int, float)) else int(last.timestamp())

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "data": data,
            "has_next": has_next,
            "next_cursor": next_cursor
        }
    finally:
        db.close()

def publish_centrifugo(channel, data):
    api_url = os.getenv("CENTRIFUGO_API_URL", "")
    api_key = os.getenv("CENTRIFUGO_API_KEY", "")
    if not api_url or not api_key:
        return
    try:
        httpx.post(
            api_url,
            headers={"Authorization": f"apikey {api_key}"},
            json={"method": "publish", "params": {"channel": channel, "data": data}},
            timeout=2,
        )
    except Exception:
        return


@app.post("/api/ohlc")
def ingest_ohlc(payload: CandleIngest | list[CandleIngest], dry: bool = False, background: BackgroundTasks = None):
    from app.api.controllers.ohlc_ingest_controller import ingest_candles, preview_candles
    candles = payload if isinstance(payload, list) else [payload]
    if TYPE != "dynamic" and not dry:
        raise HTTPException(status_code=403, detail="ingest disabled")
    try:
        if dry:
            results = preview_candles(candles, MIN_START_DATE)
        else:
            results = ingest_candles(candles, MIN_START_DATE)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
    if not dry and background is not None:
        latest = {}
        for candle, res in zip(candles, results):
            if res["action"] == "skipped":
                continue
            latest[(res["symbol"], res["timeframe"])] = candle
        for (sym, tf), candle in latest.items():
            background.add_task(publish_centrifugo, f"trade:{sym}", {
                "symbol": sym, "timeframe": tf, "open": candle.open,
                "high": candle.high, "low": candle.low,
                "close": candle.close, "time": int(candle.time),
            })
    return {"status": "ok", "results": results}

@app.get("/api/centrifugo/token")
async def centrifugo_token():
    import jwt
    from datetime import datetime, timedelta
    secret = os.getenv("CENTRIFUGO_HMAC_SECRET", "")
    payload = {
        "sub": "dashboard",
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    return {"token": token, "ws_url": os.getenv("CENTRIFUGO_URL", "ws://localhost:8000/connection/websocket")}

class PublishRequest(BaseModel):
    channel: str
    data: Any

@app.post("/api/centrifugo/publish")
async def centrifugo_publish(req: PublishRequest):
    api_url = os.getenv("CENTRIFUGO_API_URL", "https://centrifugo.devan.my.id/api")
    api_key = os.getenv("CENTRIFUGO_API_KEY", "")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            api_url,
            headers={"Authorization": f"apikey {api_key}"},
            json={"method": "publish", "params": {"channel": req.channel, "data": req.data}},
            timeout=5
        )
        return resp.json()

BRAND = APP_NAME

@app.get("/", include_in_schema=False)
async def dashboard():
    if TYPE != "dynamic":
        html = (WEB / "index.html").read_text(encoding="utf-8").replace("{{BRAND}}", BRAND)
        html = re.sub(r'\s*<div class="api-endpoint-item" data-ep="ingest">.*?</div>', "", html, flags=re.DOTALL)
        from fastapi.responses import HTMLResponse
        return HTMLResponse(html)
    return serve_page(WEB / "index.html")

WEB = Path(__file__).parent / "web"
PUBLIC = Path(__file__).parent / "public"

class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response: Response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache, max-age=0, must-revalidate"
        return response

app.mount("/css", NoCacheStaticFiles(directory=WEB / "css"), name="css")
app.mount("/javascript", NoCacheStaticFiles(directory=WEB / "javascript"), name="javascript")
app.mount("/public", NoCacheStaticFiles(directory=PUBLIC), name="public")

def serve_page(path: Path):
    html = path.read_text(encoding="utf-8").replace("{{BRAND}}", BRAND)
    from fastapi.responses import HTMLResponse
    return HTMLResponse(html)

@app.get("/{name}/{server}", include_in_schema=False)
async def symbol_page(name: str, server: str):
    return serve_page(WEB / "symbol.html")

@app.on_event("shutdown")
async def shutdown_event():
    pass

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=True
    )
