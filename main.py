import os
from pathlib import Path
import uvicorn
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import text
from pydantic import BaseModel
from typing import Any
from app.api.routes.ohlc import router as ohlc_router
# from app.api.models.configs.mt5_config import init_mt5, shutdown_mt5, get_terminal_info

load_dotenv()

PORT = int(os.getenv("PORT", "8765"))
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip()]

app = FastAPI(
    title="FOREXPOOL",
    description="API for forex market data dashboard",
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

app.include_router(ohlc_router, prefix="/api/ohlc", tags=["OHLC"])

@app.get("/api/health")
async def health_check():
    # terminal = get_terminal_info()
    return {
        "status": "healthy",
        # "mt5_connected": terminal is not None
    }

@app.get("/api/symbols")
async def symbols(search: str = None):
    from app.databases.config import SessionLocal
    db = SessionLocal()
    try:
        if search:
            rows = db.execute(text(
                "SELECT server, name FROM symbols WHERE name LIKE :q ORDER BY name ASC"
            ), {"q": f"%{search}%"}).fetchall()
        else:
            rows = db.execute(text("SELECT server, name FROM symbols ORDER BY name ASC")).fetchall()
        return {"symbols": [{"server": r[0], "name": r[1]} for r in rows]}
    finally:
        db.close()

@app.get("/api/symbols/{symbol}/range")
async def symbol_range(symbol: str):
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

@app.get("/api/symbols/{symbol}/date-range")
async def symbol_date_range(
    symbol: str,
    timeframe: str = "m1",
    start_date: str = None,
    end_date: str = None,
    limit: int = 50
):
    from app.databases.config import SessionLocal
    from sqlalchemy import text as sql_text
    from datetime import datetime

    tbl = f"ohlc_{symbol.lower()}_{timeframe.lower()}"
    db = SessionLocal()
    try:
        check = db.execute(sql_text(
            "SELECT COUNT(*) FROM information_schema.tables "
            "WHERE table_schema = DATABASE() AND table_name = :tbl"
        ), {"tbl": tbl}).scalar()
        if not check:
            return {"symbol": symbol, "timeframe": timeframe, "data": [], "total": 0}

        where_clauses = ["symbol = :sym"]
        params = {"sym": symbol}

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

        rows = db.execute(sql_text(
            f"SELECT symbol, open, high, low, close, time FROM `{tbl}` WHERE {where_sql} ORDER BY time ASC LIMIT {limit}"
        ), params).fetchall()

        total = db.execute(sql_text(
            f"SELECT COUNT(*) FROM `{tbl}` WHERE {where_sql}"
        ), params).scalar()

        def fmt(v):
            if isinstance(v, (int, float)):
                return datetime.fromtimestamp(v).strftime("%Y-%m-%d %H:%M")
            if hasattr(v, 'strftime'):
                return v.strftime("%Y-%m-%d %H:%M")
            return str(v) if v else None

        data = []
        for r in rows:
            data.append({
                "symbol": r[0],
                "open": float(r[1]) if r[1] else None,
                "high": float(r[2]) if r[2] else None,
                "low": float(r[3]) if r[3] else None,
                "close": float(r[4]) if r[4] else None,
                "time": fmt(r[5])
            })

        return {"symbol": symbol, "timeframe": timeframe, "data": data, "total": total}
    finally:
        db.close()

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

@app.get("/", include_in_schema=False)
async def dashboard():
    return FileResponse(Path(__file__).parent / "web" / "index.html")

WEB = Path(__file__).parent / "web"
app.mount("/css", StaticFiles(directory=WEB / "css"), name="css")
app.mount("/javascript", StaticFiles(directory=WEB / "javascript"), name="javascript")

@app.get("/{name}/{server}", include_in_schema=False)
async def symbol_page(name: str, server: str):
    return FileResponse(WEB / "symbol.html")

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
