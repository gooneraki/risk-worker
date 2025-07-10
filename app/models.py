"""Database models"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class TickerPrice(SQLModel, table=True):
    """Model for ticker prices"""
    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(index=True)
    price: float
    volume: Optional[float] = None
    market_cap: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def __repr__(self):
        return f"<TickerPrice(ticker='{self.ticker}', price={self.price}," + \
            f" timestamp='{self.timestamp}')>"


class TickerMetadata(SQLModel, table=True):
    """Model for ticker metadata"""
    id: Optional[int] = Field(default=None, primary_key=True)
    ticker: str = Field(unique=True, index=True)
    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    def __repr__(self):
        return f"<TickerMetadata(ticker='{self.ticker}', company_name='{self.company_name}')>"
