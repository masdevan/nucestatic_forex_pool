from app.databases.config import Base
from sqlalchemy import Column, Integer, DateTime
from datetime import datetime

class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

class IDMixin:
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)