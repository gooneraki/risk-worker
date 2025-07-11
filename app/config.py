"""Application settings"""
import os
import socket
from dotenv import load_dotenv


class Settings:
    """Application settings - mix of environment variables and constants"""

    # Constants - same for all environments
    YF_TIMEOUT = 10
    YF_RETRY_ATTEMPTS = 3
    REDIS_CHANNEL = "ticker_updates"

    def __init__(self, env_file: str | None = None):
        """Initialize settings, loading from .env file or specified env file"""
        if env_file is not None:
            load_dotenv(env_file)
        else:
            # Default to loading .env file if it exists
            if os.path.exists('.env'):
                load_dotenv('.env')

        # Database settings (required)
        self.database_url: str = self._get_required_env("DATABASE_URL")

        # Redis settings - auto-detect Redis vs FakeRedis
        self.use_fake_redis: bool = self._should_use_fake_redis()

        # Set Redis URL based on whether we're using fake or real Redis
        if self.use_fake_redis:
            self.redis_url = "fake://localhost"  # Placeholder for FakeRedis
        else:
            self.redis_url = "redis://redis:6379"

        # Application settings (required)
        self.log_level: str = self._get_required_env("LOG_LEVEL")
        self.worker_name: str = self._get_required_env("WORKER_NAME")
        self.log_file: str = self._get_required_env("LOG_FILE")

        # API settings (required)
        self.api_host: str = self._get_required_env("API_HOST")
        self.api_port: int = int(self._get_required_env("API_PORT"))

    def _get_required_env(self, key: str) -> str:
        """Get required environment variable or raise error"""
        value = os.getenv(key)
        if value is None:
            raise ValueError(f"Required environment variable '{key}' is not set. "
                             f"Please create a .env file or set the environment variable. "
                             f"See environment.example for reference.")
        return value

    def _should_use_fake_redis(self) -> bool:
        """Auto-detect if we should use FakeRedis or real Redis"""
        # Check if Redis is available - if not, use FakeRedis
        redis_available = self._check_redis_available()

        if not redis_available:
            print("🔍 Redis not detected - using FakeRedis (in-memory)")
        else:
            print("🔍 Redis detected - using real Redis server")

        return not redis_available

    def _check_redis_available(self) -> bool:
        """Check if Redis is available on redis:6379"""
        try:
            with socket.create_connection(('redis', 6379), timeout=1):
                return True
        except (socket.error, socket.timeout):
            return False

    def get_database_url(self) -> str:
        """Get database URL"""
        return self.database_url

    def get_redis_url(self) -> str:
        """Get Redis URL"""
        return self.redis_url

    def get_redis_client(self):
        """Get Redis client - either real Redis or FakeRedis (async compatible)"""
        if self.use_fake_redis:
            # Import fakeredis.aioredis for async compatibility
            import fakeredis.aioredis
            return fakeredis.aioredis.FakeRedis()
        else:
            import redis.asyncio as redis
            return redis.from_url(self.redis_url)

    @property
    def yf_timeout(self) -> int:
        """yFinance timeout (constant)"""
        return self.YF_TIMEOUT

    @property
    def yf_retry_attempts(self) -> int:
        """yFinance retry attempts (constant)"""
        return self.YF_RETRY_ATTEMPTS

    @property
    def redis_channel(self) -> str:
        """Redis channel (constant)"""
        return self.REDIS_CHANNEL


# Global settings instance
settings = Settings()
