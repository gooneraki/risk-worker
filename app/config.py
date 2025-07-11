"""Application configuration with environment-based settings"""
import os
import socket
from dotenv import load_dotenv


class Settings:
    """Application configuration loaded from environment variables"""

    # Constants
    YF_TIMEOUT = 10
    YF_RETRY_ATTEMPTS = 3
    REDIS_CHANNEL = "ticker_updates"

    def __init__(self, env_file: str | None = None):
        """Load settings from environment file or system env"""
        if env_file:
            load_dotenv(env_file)
        elif os.path.exists('.env'):
            load_dotenv('.env')

        # Required settings
        self.database_url: str = self._get_required_env("DATABASE_URL")
        self.log_level: str = self._get_required_env("LOG_LEVEL")
        self.worker_name: str = self._get_required_env("WORKER_NAME")
        self.log_file: str = self._get_required_env("LOG_FILE")
        self.api_host: str = self._get_required_env("API_HOST")
        self.api_port: int = int(self._get_required_env("API_PORT"))

        # Redis configuration - support both URL and individual params
        self.redis_url: str = self._get_redis_url()
        self.use_fake_redis: bool = self._should_use_fake_redis()

    def _get_required_env(self, key: str) -> str:
        """Get required environment variable or raise error"""
        value = os.getenv(key)
        if value is None:
            raise ValueError(f"Required environment variable '{key}' not set. "
                             f"See environment.example for reference.")
        return value

    def _get_redis_url(self) -> str:
        """Get Redis URL - either from REDIS_URL env var or construct from components"""
        # First check for full Redis URL (for production/Upstash)
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            return redis_url

        # Fallback to individual components (for local development)
        redis_host = os.getenv("REDIS_HOST", "redis")
        redis_port = os.getenv("REDIS_PORT", "6379")
        redis_password = os.getenv("REDIS_PASSWORD")
        redis_db = os.getenv("REDIS_DB", "0")

        if redis_password:
            return f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
        else:
            return f"redis://{redis_host}:{redis_port}/{redis_db}"

    def _should_use_fake_redis(self) -> bool:
        """Auto-detect Redis availability"""
        # If we have a Redis URL (production), don't use fake Redis
        if os.getenv("REDIS_URL"):
            return False

        # For local development, check if Redis is available
        redis_available = self._check_redis_available()
        return not redis_available

    def _check_redis_available(self) -> bool:
        """Check if Redis is available on redis:6379"""
        try:
            redis_host = os.getenv("REDIS_HOST", "redis")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            with socket.create_connection((redis_host, redis_port), timeout=1):
                return True
        except (socket.error, socket.timeout):
            return False

    def get_redis_client(self):
        """Get Redis client - real or fake based on availability"""
        if self.use_fake_redis:
            import fakeredis.aioredis
            return fakeredis.aioredis.FakeRedis()
        else:
            import redis.asyncio as redis
            # For Upstash/TLS connections, configure SSL properly
            if self.redis_url.startswith("rediss://") or os.getenv("REDIS_TLS", "false").lower() == "true":
                return redis.from_url(self.redis_url, ssl_cert_reqs=None)
            else:
                return redis.from_url(self.redis_url)

    @property
    def yf_timeout(self) -> int:
        """Get Yahoo Finance timeout"""
        return self.YF_TIMEOUT

    @property
    def yf_retry_attempts(self) -> int:
        """Get Yahoo Finance retry attempts"""
        return self.YF_RETRY_ATTEMPTS

    @property
    def redis_channel(self) -> str:
        """Get Redis channel"""
        return self.REDIS_CHANNEL


# Global settings instance
settings = Settings()
