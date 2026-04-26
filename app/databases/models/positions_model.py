from sqlalchemy import Column, Integer, String, DateTime, Numeric, BigInteger
from app.databases.config import Base

class Positions(Base):
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket = Column(BigInteger)
    symbol = Column(String(50))
    type = Column(String(20))
    volume = Column(Numeric(10, 2))
    price = Column(Numeric(10, 5))
    sl = Column(Numeric(10, 5))
    tp = Column(Numeric(10, 5))
    profit = Column(Numeric(15, 2))
    closed_by = Column(String(50))
    time = Column(String(50))
    is_running = Column(Integer, default=1)
    created_at = Column(DateTime, default=None)
    updated_at = Column(DateTime, default=None)