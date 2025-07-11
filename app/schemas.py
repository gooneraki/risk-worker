"""Pydantic schemas for API responses and internal data transfer"""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel


class TickerPriceResponse(SQLModel):
    """API response schema for ticker price"""
    ticker: str
    price: float
    volume: Optional[float] = None
    market_cap: Optional[float] = None
    timestamp: datetime


class TickerMetadataResponse(SQLModel):
    """API response schema for ticker metadata"""
    ticker: str
    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    last_updated: datetime


class PriceFetchResult(SQLModel):
    """Internal schema for price fetch operations"""
    ticker: str
    price: float
    volume: Optional[float] = None
    market_cap: Optional[float] = None
    success: bool
    error_message: Optional[str] = None
