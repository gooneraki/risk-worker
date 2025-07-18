"""Redis service for Pub/Sub functionality."""
import json
import asyncio
import logging
from typing import Optional
import redis.asyncio as redis
from app.config import settings

# Channel names
TICKER_UPDATES_CHANNEL = "ticker_updates"
TICKER_PRICE_UPDATES_CHANNEL = "ticker_price_updates"

logger = logging.getLogger(__name__)


class RedisService:
    """Redis service for handling Pub/Sub operations."""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.is_fake_redis = False

    async def connect(self):
        """Connect to Redis based on environment."""

        if settings.env == "dev":
            # ENV=dev -> Use FakeRedis (no external Redis needed)
            await self._connect_fake_redis()

        elif settings.env == "docker":
            # ENV=docker -> Use Redis container from docker-compose
            await self._connect_docker_redis()

        elif settings.env == "prod":
            # ENV=prod -> Use Upstash Redis (cloud)
            await self._connect_upstash_redis()

        else:
            raise ValueError(f"Unknown environment: {settings.env}")

    async def _connect_fake_redis(self):
        """Connect to FakeRedis for local development."""
        try:
            import fakeredis.aioredis
            self.redis_client = fakeredis.aioredis.FakeRedis(
                decode_responses=True
            )
            self.is_fake_redis = True

            # Test FakeRedis connection
            await self.redis_client.ping()
            logger.info("FakeRedis connected [ENV=dev]")

        except Exception as e:
            logger.error("FakeRedis connection failed: %s", e)
            raise

    async def _connect_docker_redis(self):
        """Connect to Redis container in Docker environment."""
        try:
            self.redis_client = redis.Redis(
                host=settings.redis_config.host,
                port=settings.redis_config.port,
                db=0,
                password=settings.redis_config.password,
                ssl=settings.redis_config.tls == "true",
                decode_responses=True,
                socket_connect_timeout=5,  # Docker might be slower
                socket_timeout=5
            )

            # Test the connection
            await asyncio.wait_for(self.redis_client.ping(), timeout=5.0)
            logger.info("Redis connected [ENV=docker] %s:%s",
                        settings.redis_config.host, settings.redis_config.port)

        except Exception as e:
            logger.error("Docker Redis connection failed: %s", e)
            raise

    async def _connect_upstash_redis(self):
        """Connect to Upstash Redis for production."""
        try:
            if not settings.redis_config.url:
                raise ValueError(
                    "REDIS_URL is required for production environment")

            self.redis_client = redis.from_url(settings.redis_config.url)

            # Test the connection
            await asyncio.wait_for(self.redis_client.ping(), timeout=10.0)
            logger.info("Upstash Redis connected [ENV=prod] TLS:%s",
                        settings.redis_config.tls)

        except Exception as e:
            logger.error("Upstash Redis connection failed: %s", e)
            raise

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")

    async def publish_ticker_update(self, ticker: str, user_id: int, action: str = "add"):
        """Publish a ticker update event to Redis."""
        if not self.redis_client:
            await self.connect()

        assert self.redis_client is not None
        message = {
            "ticker": ticker.upper(),
            "user_id": user_id,
            "action": action,  # "add", "update", "delete"
            "timestamp": asyncio.get_event_loop().time()
        }

        try:
            await self.redis_client.publish(
                TICKER_UPDATES_CHANNEL,
                json.dumps(message)
            )
        except Exception as e:
            logger.error("Failed to publish ticker update: %s", e)
            raise

    async def publish_price_update(self, ticker: str, price: float, timestamp: float):
        """Publish a price update event to Redis."""
        if not self.redis_client:
            await self.connect()

        assert self.redis_client is not None
        message = {
            "ticker": ticker.upper(),
            "price": price,
            "timestamp": timestamp
        }

        try:
            await self.redis_client.publish(
                TICKER_PRICE_UPDATES_CHANNEL,
                json.dumps(message)
            )
        except Exception as e:
            logger.error("Failed to publish price update: %s", e)
            raise

    async def get_latest_price(self, ticker: str) -> Optional[float]:
        """Get the latest price for a ticker from Redis cache."""
        if not self.redis_client:
            await self.connect()

        assert self.redis_client is not None
        try:
            price_key = f"price:{ticker.upper()}"
            price = await self.redis_client.get(price_key)
            return float(price) if price else None
        except Exception as e:
            logger.error("Failed to get latest price for %s: %s", ticker, e)
            return None

    async def set_latest_price(self, ticker: str, price: float, expiry: int = 300):
        """Set the latest price for a ticker in Redis cache."""
        if not self.redis_client:
            await self.connect()

        assert self.redis_client is not None
        try:
            price_key = f"price:{ticker.upper()}"
            await self.redis_client.setex(price_key, expiry, str(price))
        except Exception as e:
            logger.error("Failed to cache price for %s: %s", ticker, e)

    async def get_redis_info(self) -> dict:
        """Get Redis information for debugging."""
        if not self.redis_client:
            await self.connect()

        assert self.redis_client is not None
        try:
            info = {
                "is_fake_redis": self.is_fake_redis,
                "redis_type": "FakeRedis (in-memory)" if self.is_fake_redis else "Real Redis",
                "connection_status": "connected" if self.redis_client else "disconnected",
                "fallback_used": self.is_fake_redis
            }

            if not self.is_fake_redis:
                # Only real Redis has these info commands
                ping_result = await self.redis_client.ping()
                info["ping"] = ping_result

            return info
        except Exception as e:
            return {
                "is_fake_redis": self.is_fake_redis,
                "redis_type": "FakeRedis (in-memory)" if self.is_fake_redis else "Real Redis",
                "connection_status": "error",
                "fallback_used": self.is_fake_redis,
                "error": str(e)
            }

    async def subscribe_to_channel(self, channel: str):
        """Subscribe to a Redis channel and return the pubsub object."""
        if not self.redis_client:
            await self.connect()

        assert self.redis_client is not None
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe(channel)
        return pubsub


# Global Redis service instance
redis_service = RedisService()
