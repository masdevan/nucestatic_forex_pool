from sqlalchemy import Column, Integer, String, DateTime, Text
from app.databases.config import Base

class News(Base):
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    time = Column(DateTime)
    title = Column(String(500))
    url = Column(String(500))
    description = Column(Text)
    description_status = Column(Integer, default=0)
    score = Column(Integer, default=0)
    pair_impact = Column(String(255), default="")
    direction = Column(String(50), default="")
    reason = Column(String(500), default="")
    created_at = Column(DateTime, default=None)
    updated_at = Column(DateTime, default=None)
