"""Utility functions for the application"""
import os
from dotenv import load_dotenv

load_dotenv()


def get_required_env(key: str) -> str:
    """Get required environment variable or raise error"""
    value = os.getenv(key)
    if value is None:
        raise ValueError(f"Required environment variable '{key}' not set. "
                         f"See env.example for reference.")
    return value
