from sqlalchemy import text

BLOCK = 1000


def rebuild_anchors(symbol, timeframe, conn):
    tbl = f"ohlc_{symbol.lower()}_{timeframe.lower()}"
    label = timeframe.upper()
    conn.execute(
        text("DELETE FROM ohlc_page_anchor WHERE symbol = :sym AND timeframe = :tf"),
        {"sym": symbol, "tf": label},
    )
    conn.execute(
        text(
            f"INSERT INTO ohlc_page_anchor (symbol, timeframe, k, start_time) "
            f"SELECT :sym, :tf, k, MIN(time) FROM ("
            f"SELECT time, FLOOR((ROW_NUMBER() OVER (ORDER BY time) - 1) / {BLOCK}) AS k "
            f"FROM `{tbl}` WHERE symbol = :sym) x GROUP BY k"
        ),
        {"sym": symbol, "tf": label},
    )


def ensure_anchor(symbol, timeframe, conn, before_count, row_start_time):
    if before_count % BLOCK != 0:
        return
    conn.execute(
        text("INSERT IGNORE INTO ohlc_page_anchor (symbol, timeframe, k, start_time) "
             "VALUES (:sym, :tf, :k, :t)"),
        {"sym": symbol, "tf": timeframe.upper(),
         "k": before_count // BLOCK, "t": row_start_time},
    )