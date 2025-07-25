"""Core business logic for ticker price processing"""
import logging
from datetime import datetime
from typing import Optional
import yfinance as yf
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, desc

from app.models import TickerPrice, TickerMetadata
from app.schemas import PriceFetchResult
from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def fetch_price_from_yfinance(ticker: str) -> PriceFetchResult:
    """Fetch current price data from yFinance"""
    try:
        yf_ticker = yf.Ticker(ticker)
        info = yf_ticker.info
        hist = yf_ticker.history(period="1d")

        if hist.empty:
            logger.warning("No price data available for %s", ticker)
            return PriceFetchResult(
                ticker=ticker,
                price=0.0,
                success=False,
                error_message="No price data available"
            )

        # Extract latest price data
        latest = hist.iloc[-1]
        price = float(latest['Close'])
        volume = float(latest['Volume']) if 'Volume' in latest else None
        market_cap = info.get('marketCap', None)

        logger.debug("Fetched price for %s: $%.2f", ticker, price)

        return PriceFetchResult(
            ticker=ticker,
            price=price,
            volume=volume,
            market_cap=market_cap,
            success=True
        )

    except Exception as e:
        logger.error("Error fetching price for %s: %s", ticker, str(e))
        return PriceFetchResult(
            ticker=ticker,
            price=0.0,
            success=False,
            error_message=str(e)
        )


async def store_price_in_db(session: AsyncSession, price_result: PriceFetchResult) -> bool:
    """Store price data in database"""
    try:
        price_record = TickerPrice(
            ticker=price_result.ticker,
            price=price_result.price,
            volume=price_result.volume,
            market_cap=price_result.market_cap,
            timestamp=datetime.utcnow()
        )

        session.add(price_record)
        await session.commit()

        logger.debug("Stored price for %s in database", price_result.ticker)
        return True

    except Exception as e:
        logger.error("Error storing price for %s: %s",
                     price_result.ticker, str(e))
        await session.rollback()
        return False


async def update_ticker_metadata(session: AsyncSession, ticker: str) -> bool:
    """Update or create ticker metadata"""
    try:
        yf_ticker = yf.Ticker(ticker)
        info = yf_ticker.info

        # Check for existing metadata
        stmt = select(TickerMetadata).where(TickerMetadata.ticker == ticker)
        result = await session.execute(stmt)
        existing_metadata = result.scalar_one_or_none()

        if existing_metadata:
            # Update existing
            existing_metadata.company_name = info.get(
                'longName', existing_metadata.company_name)
            existing_metadata.sector = info.get(
                'sector', existing_metadata.sector)
            existing_metadata.industry = info.get(
                'industry', existing_metadata.industry)
            existing_metadata.last_updated = datetime.utcnow()
            logger.debug("Updated metadata for %s", ticker)
        else:
            # Create new
            metadata = TickerMetadata(
                ticker=ticker,
                company_name=info.get('longName'),
                sector=info.get('sector'),
                industry=info.get('industry'),
                last_updated=datetime.utcnow()
            )
            session.add(metadata)
            logger.debug("Created metadata for %s", ticker)

        await session.commit()
        return True

    except Exception as e:
        logger.error("Error updating metadata for %s: %s", ticker, str(e))
        await session.rollback()
        return False


async def process_ticker_event(ticker: str):
    """Main ticker processing pipeline"""
    logger.info("Processing ticker: %s", ticker)

    try:
        # Fetch price from yFinance
        price_result = await fetch_price_from_yfinance(ticker)

        if not price_result.success:
            logger.error("Failed to fetch price for %s: %s",
                         ticker, price_result.error_message)
            return

        # Store in database
        async with AsyncSessionLocal() as session:
            price_stored = await store_price_in_db(session, price_result)
            metadata_updated = await update_ticker_metadata(session, ticker)

            if price_stored and metadata_updated:
                logger.info("Successfully processed %s: $%.2f",
                            ticker, price_result.price)
            else:
                logger.warning("Partial success processing %s", ticker)

    except Exception as e:
        logger.error("Error processing ticker %s: %s", ticker, str(e))
