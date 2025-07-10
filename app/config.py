"""Application settings"""
import os


class Settings:
    """Application settings loaded from environment variables"""

    # Database settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:password@postgres:5432/risk_metrics"
    )

    # Redis settings
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379")
    REDIS_CHANNEL: str = os.getenv("REDIS_CHANNEL", "ticker_updates")

    # Application settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    WORKER_NAME: str = os.getenv("WORKER_NAME", "risk-worker")

    # yFinance settings
    YF_TIMEOUT: int = int(os.getenv("YF_TIMEOUT", "10"))
    YF_RETRY_ATTEMPTS: int = int(os.getenv("YF_RETRY_ATTEMPTS", "3"))

    # API settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

    @classmethod
    def get_database_url(cls) -> str:
        """Get database URL with fallback"""
        return cls.DATABASE_URL

    @classmethod
    def get_redis_url(cls) -> str:
        """Get Redis URL with fallback"""
        return cls.REDIS_URL


# Create settings instance
settings = Settings()
