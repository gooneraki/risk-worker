"""Main application module - FastAPI worker with Redis subscription"""
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

# Setup logging with rotation
os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)

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

# Redis client and channel
redis_client = settings.get_redis_client()
REDIS_CHANNEL = settings.redis_channel


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Handle startup and shutdown events"""
    logger.info("Starting Risk Worker v1.0 - %s", settings.worker_name)
    logger.info("Configuration: API %s:%d, Redis: %s",
                settings.api_host, settings.api_port,
                "FakeRedis" if settings.use_fake_redis else "Redis")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database: %s", e)
        raise

    # Start Redis subscription
    task = asyncio.create_task(subscribe_to_tickers())
    logger.info("Redis subscription started")

    yield

    # Cleanup on shutdown
    logger.info("Shutting down Risk Worker")
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    logger.info("Shutdown complete")


app = FastAPI(title="Risk Worker",
              description="Async worker for processing ticker price updates",
              lifespan=lifespan)


@app.get("/healthz")
def healthz():
    """Health check endpoint"""
    return {"status": "ok", "service": "risk-worker", "worker": settings.worker_name}


@app.get("/latest-price/{ticker}", response_model=TickerPrice)
async def get_latest_ticker_price(ticker: str, db: AsyncSession = Depends(get_db)):
    """Get latest price for a ticker"""
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
    """Manually trigger price update for a ticker"""
    try:
        logger.info("Manual trigger for %s", ticker)
        await process_ticker_event(ticker.upper())
        return {"message": f"Update triggered for {ticker}", "status": "success"}
    except Exception as e:
        logger.error("Error triggering update for %s: %s", ticker, e)
        raise HTTPException(
            status_code=500, detail="Failed to trigger update") from e


async def subscribe_to_tickers():
    """Subscribe to Redis ticker updates and process them"""
    while True:
        try:
            pubsub = redis_client.pubsub()
            await pubsub.subscribe(REDIS_CHANNEL)

            logger.info("Subscribed to Redis channel: %s", REDIS_CHANNEL)

            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        # Parse JSON message from risk-api
                        import json
                        message_data = json.loads(message['data'].decode())
                        ticker = message_data.get('ticker', '').strip().upper()
                        action = message_data.get('action', 'add')
                        
                        if ticker:
                            logger.info("Received ticker event: %s (action: %s)", ticker, action)
                            await process_ticker_event(ticker)
                        else:
                            logger.warning("Empty ticker in message: %s", message_data)
                    except json.JSONDecodeError:
                        # Fallback to simple string format
                        ticker = message['data'].decode().strip().upper()
                        if ticker:
                            logger.info("Received ticker event (simple): %s", ticker)
                            await process_ticker_event(ticker)
                    except Exception as e:
                        logger.error("Error processing ticker message: %s", e)
        except Exception as e:
            logger.error("Redis subscription error: %s", e)
            await asyncio.sleep(5)  # Wait before retrying
        finally:
            try:
                await pubsub.close()
            except Exception:
                pass
            logger.info("Restarting Redis subscription...")
