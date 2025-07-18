"""Application configuration with environment-based settings"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class RedisConfig:
    """Redis configuration settings."""
    host: str
    port: int
    user: str
    password: str
    domain: str
    tls: str
    url: str = ""

    def __post_init__(self):
        self.url = f"{self.domain}://{self.user}:{self.password}@{self.host}:{self.port}" if \
            self.user and self.password else \
            f"{self.domain}://{self.host}:{self.port}"


class Settings:
    """Application configuration loaded from environment variables"""

    # Constants
    REDIS_CHANNEL = "ticker_updates"

    def __init__(self, env_file: str | None = None):
        """Load settings from environment file or system env"""
        if env_file:
            load_dotenv(env_file)
        elif os.path.exists('.env'):
            load_dotenv('.env')

        # Environment detection
        self.env = os.getenv("ENV", "dev")

        # Required settings
        self.database_url: str = self._convert_db_url_for_async(
            self._get_required_env("DATABASE_URL"))

        # Simple security for server-to-server communication
        self.worker_secret: str = self._get_required_env("WORKER_SECRET")

        # Redis configuration based on environment
        if self.env == "prod":
            self.redis_config = RedisConfig(
                host=self._get_env_var("REDIS_HOST"),
                port=int(self._get_env_var("REDIS_PORT")),
                user=self._get_env_var("REDIS_USER"),
                password=self._get_env_var("REDIS_PASSWORD"),
                domain=self._get_env_var("REDIS_DOMAIN"),
                tls=self._get_env_var("REDIS_TLS"),
            )
        elif self.env == "docker":
            self.redis_config = RedisConfig(
                host=self._get_env_var("REDIS_HOST"),
                port=int(self._get_env_var("REDIS_PORT")),
                user="",
                password="",
                domain=self._get_env_var("REDIS_DOMAIN"),
                tls=self._get_env_var("REDIS_TLS"),
            )

    def _get_env_var(self, key: str, default: str = "") -> str:
        """Get environment variable with default"""
        return os.getenv(key, default)

    def _get_required_env(self, key: str) -> str:
        """Get required environment variable or raise error"""
        value = os.getenv(key)
        if value is None:
            raise ValueError(f"Required environment variable '{key}' not set. "
                             f"See environment.example for reference.")
        return value

    def _convert_db_url_for_async(self, db_url: str) -> str:
        """Convert database URL to use async driver if needed"""
        # Convert postgresql:// to postgresql+asyncpg:// for async compatibility
        if db_url.startswith('postgresql://'):
            return db_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
        # Keep other formats (like sqlite+aiosqlite://) as-is
        return db_url

    @property
    def redis_channel(self) -> str:
        """Get Redis channel"""
        return self.REDIS_CHANNEL


# Global settings instance
settings = Settings()
