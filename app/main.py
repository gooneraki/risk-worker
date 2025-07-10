"""Main application module"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db, init_db
from app.metrics import process_ticker_event, get_latest_price
from app.models import TickerPrice

# Ensure logs directory exists
os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)

# Configure log rotation
rotating_handler = RotatingFileHandler(
    settings.log_file,
    maxBytes=1*1024*1024,
    backupCount=10,
    encoding='utf-8'
)

console_handler = logging.StreamHandler()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[rotating_handler, console_handler],
    force=True
)
logger = logging.getLogger(__name__)

# Redis setup - use the smart Redis client
redis_client = settings.get_redis_client()
REDIS_CHANNEL = settings.redis_channel


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Handle startup and shutdown events"""
    logger.info("Starting risk worker...")

    # Initialize database tables
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database: %s", e)
        raise

    # Start Redis subscription in background
    task = asyncio.create_task(subscribe_to_tickers())

    yield

    # Cleanup on shutdown
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Risk Worker",
              description="Async worker for processing ticker price updates",
              lifespan=lifespan)


@app.get("/healthz")
def healthz():
    """Health check endpoint"""
    return {"status": "ok", "service": "risk-worker"}


@app.get("/latest-price/{ticker}", response_model=TickerPrice)
async def get_latest_ticker_price(ticker: str, db: AsyncSession = Depends(get_db)):
    """Get the latest price for a specific ticker"""
    try:
        price_record = await get_latest_price(db, ticker.upper())

        if not price_record:
            raise HTTPException(
                status_code=404, detail=f"No price data found for {ticker}")

        return price_record

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching latest price for %s: %s", ticker, e)
        raise HTTPException(
            status_code=500, detail="Internal server error") from e


@app.post("/trigger-update/{ticker}")
async def trigger_ticker_update(ticker: str):
    """Manually trigger a price update for a ticker"""
    try:
        logger.info("Triggering update for %s", ticker)
        await process_ticker_event(ticker.upper())
        return {"message": f"Update triggered for {ticker}", "status": "success"}
    except Exception as e:
        logger.error("Error triggering update for %s: %s", ticker, e)
        raise HTTPException(
            status_code=500, detail="Failed to trigger update") from e


async def subscribe_to_tickers():
    """Subscribe to Redis ticker updates channel"""
    while True:
        try:
            pubsub = redis_client.pubsub()
            await pubsub.subscribe(REDIS_CHANNEL)

            logger.info("Subscribed to Redis channel: %s", REDIS_CHANNEL)

            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        ticker = message['data'].decode().strip().upper()
                        logger.info("Received ticker update: %s", ticker)
                        await process_ticker_event(ticker)
                        logger.info("Processed ticker update: %s", ticker)
                    except Exception as e:
                        logger.error("Error processing ticker message: %s", e)
        except Exception as e:
            logger.error("Redis subscription error: %s", e)
            # Wait before retrying
            await asyncio.sleep(5)
        finally:
            try:
                await pubsub.close()
            except Exception:
                pass
            logger.info("Restarting Redis subscription loop...")
