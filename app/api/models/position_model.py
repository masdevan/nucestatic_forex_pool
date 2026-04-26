from typing import List, Optional
from pydantic import BaseModel

class PositionInfo(BaseModel):
    ticket: int
    time: int
    time_str: str
    type: int
    type_str: str
    magic: int
    identifier: int
    volume: float
    price_open: float
    price_current: float
    sl: float
    tp: float
    profit: float
    symbol: str
    comment: str

class PositionsResponse(BaseModel):
    positions: List[PositionInfo]
    total: int

class PositionResponse(BaseModel):
    ticket: int
    symbol: str
    volume: float
    type: str
    price_open: float
    price_current: float
    sl: float
    tp: float
    profit: float
    comment: str

class OpenMarketRequest(BaseModel):
    symbol: str
    volume: float
    type: str
    sl: Optional[float] = None
    tp: Optional[float] = None
    comment: Optional[str] = ""
    magic: Optional[int] = 0

class OpenLimitRequest(BaseModel):
    symbol: str
    volume: float
    type: str
    price: float
    sl: Optional[float] = None
    tp: Optional[float] = None
    comment: Optional[str] = ""
    magic: Optional[int] = 0

class ClosePositionRequest(BaseModel):
    ticket: int

class ModifyPositionRequest(BaseModel):
    ticket: int
    sl: Optional[float] = None
    tp: Optional[float] = None
    volume: Optional[float] = None

class ActionResponse(BaseModel):
    success: bool
    message: str
    ticket: Optional[int] = None

class HistoryDealInfo(BaseModel):
    ticket: int
    time: int
    time_str: str
    time_msc: int
    type: int
    type_str: str
    magic: int
    order: int
    position_id: int
    volume: float
    price: float
    sl: float
    tp: float
    commission: float
    fee: float
    profit: float
    symbol: str
    comment: str
    external_id: str

class HistoryOrderInfo(BaseModel):
    ticket: int
    time_setup: int
    time_setup_str: str
    time_expiration: int
    type: int
    type_str: str
    magic: int
    volume_current: float
    volume_original: float
    price_open: float
    price_current: float
    sl: float
    tp: float
    position_id: int
    comment: str

class HistoryResponse(BaseModel):
    deals: List[HistoryDealInfo]
    orders: List[HistoryOrderInfo]
    total_deals: int
    total_orders: int

class DBPositionInfo(BaseModel):
    id: int
    ticket: int
    symbol: str
    type: str
    volume: float
    price: float
    sl: Optional[float] = None
    tp: Optional[float] = None
    profit: float
    closed_by: Optional[str] = None
    time: str
    is_running: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class DBPositionInfoRaw(BaseModel):
    id: int
    ticket: int
    symbol: str
    type: str
    volume: float
    price: float
    sl: Optional[float] = None
    tp: Optional[float] = None
    profit: float
    closed_by: Optional[str] = None
    time: Optional[str] = None
    is_running: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class DBPositionsResponse(BaseModel):
    positions: List[DBPositionInfoRaw]
    total: int
    page: int
    per_page: int
    total_pages: int