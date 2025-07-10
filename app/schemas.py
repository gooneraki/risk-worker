"""API response schemas"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel


class TickerPriceResponse(SQLModel):
    """Response schema for ticker price"""
    ticker: str
    price: float
    volume: Optional[float] = None
    market_cap: Optional[float] = None
    timestamp: datetime


class TickerMetadataResponse(SQLModel):
    """Response schema for ticker metadata"""
    ticker: str
    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    last_updated: datetime


class PriceFetchResult(SQLModel):
    """Result schema for price fetch operations"""
    ticker: str
    price: float
    volume: Optional[float] = None
    market_cap: Optional[float] = None
    success: bool
    error_message: Optional[str] = None
