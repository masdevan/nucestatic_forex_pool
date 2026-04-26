from pydantic import BaseModel

class AccountInfo(BaseModel):
    login: int
    trade_mode: int
    leverage: int
    balance: float
    credit: float
    profit: float
    equity: float
    margin: float
    margin_free: float
    margin_level: float
    server: str
    currency: str
    company: str
    name: str
    demo: int

class AccountResponse(BaseModel):
    account: AccountInfo