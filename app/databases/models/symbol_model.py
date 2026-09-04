from sqlalchemy import Column, Integer, String, TIMESTAMP, UniqueConstraint, func
from app.databases.config import Base

class Symbol(Base):
    __tablename__ = "symbols"
    __table_args__ = (
        UniqueConstraint("server", "name", name="unique_symbol_server"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    server = Column(String(100), nullable=False, default="")
    name = Column(String(100), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
