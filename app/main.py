"""Main application module - FastAPI worker with Redis subscription"""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession


from app.logger_service import logger
from app.config import settings
from app.database import get_db, init_db
from app.metrics import process_ticker_event, get_latest_price
from app.models import TickerPrice
from app.redis_service import redis_service
# Redis client and channel
REDIS_CHANNEL = settings.redis_channel

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Handle startup and shutdown events"""
    logger.info("--------------------------------")
    logger.info("Starting Risk Worker")

    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database: %s", e)
        raise

    # Initialize Redis connection
    try:
        await redis_service.connect()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error("Redis connection failed: %s", e)
        raise

    yield

    try:
        await redis_service.disconnect()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.error("Redis connection failed: %s", e)

    logger.info("Shutdown complete")


app = FastAPI(title="Risk Worker",
              description="Async worker for processing ticker price updates",
              lifespan=lifespan)


def verify_shared_secret(x_worker_secret: str = Header(None)):
    """Simple security check for server-to-server communication"""
    if x_worker_secret != settings.worker_secret:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


@app.get("/healthz")
def healthz():
    """Health check endpoint"""
    return {"status": "ok", "service": "risk-worker"}


@app.get("/")
@app.head("/")
def root():
    """Root endpoint - API information"""
    return {
        "service": "risk-worker",
        "description": "Async worker for processing ticker price updates",
        "endpoints": {
            "health": "/healthz",
            "docs": "/docs",
            "latest_price": "/latest-price/{ticker}",
            "trigger_update": "/trigger-update/{ticker}"
        },
        "status": "running"
    }


@app.get("/latest-price/{ticker}", response_model=TickerPrice)
async def get_latest_ticker_price(
    ticker: str,
    db: AsyncSession = Depends(get_db),
    _: bool = Depends(verify_shared_secret)
):
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
async def trigger_ticker_update(
    ticker: str,
    _: bool = Depends(verify_shared_secret)
):
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
            pubsub = await redis_service.subscribe_to_channel(REDIS_CHANNEL)
            logger.info("Subscribed to Redis channel: %s", REDIS_CHANNEL)

            # Start the subscription loop
            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        # Parse JSON message from risk-api
                        import json
                        message_data = json.loads(message['data'].decode())

                        ticker = message_data.get('ticker', '').strip().upper()
                        action = message_data.get('action', 'add')

                        if ticker:
                            logger.info(
                                "Received ticker event: %s (action: %s)", ticker, action)
                            await process_ticker_event(ticker)
                        else:
                            logger.warning(
                                "Empty ticker in message: %s", message_data)
                    except json.JSONDecodeError:
                        # Fallback to simple string format
                        ticker = message['data'].decode().strip().upper()
                        if ticker:
                            logger.info(
                                "Received ticker event (simple): %s", ticker)
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
