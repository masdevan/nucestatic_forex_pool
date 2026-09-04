from typing import List
from pydantic import BaseModel

class OHLCData(BaseModel):
    time: int
    open: float
    high: float
    low: float
    close: float

class OHLCResponse(BaseModel):
    pair: str
    timeframe: str
    start_date: str
    end_date: str
    data: List[OHLCData]
    total_records: int
