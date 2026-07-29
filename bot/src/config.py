from pydantic_settings import BaseSettings
from typing import Optional


class BotSettings(BaseSettings):
    api_base_url: str = "http://backend:8000/api"
    api_key: Optional[str] = None
    redis_url: str = "redis://redis:6379/0"
    log_level: str = "INFO"
    polling_interval_seconds: int = 30
    max_retries: int = 3

    class Config:
        env_file = ".env"
        env_prefix = "BOT_"
