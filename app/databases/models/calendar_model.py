from sqlalchemy import Column, Integer, String, DateTime, Text
from app.databases.config import Base

class Calendar(Base):
    __tablename__ = "calendars"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(String(50))
    currency = Column(String(10))
    event = Column(String(500))
    url = Column(String(500))
    impact = Column(String(20))
    actual = Column(String(50))
    forecast = Column(String(50))
    previous = Column(String(50))
    description = Column(Text)
    description_status = Column(Integer, default=0)
    created_at = Column(DateTime, default=None)
    updated_at = Column(DateTime, default=None)