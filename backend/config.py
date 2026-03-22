from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    BOT_TOKEN: str = "your_bot_token"
    WEBAPP_URL: str = "http://localhost:8000"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    DATA_DIR: str = "./data/schedule"
    CACHE_TTL: int = 3600
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def data_path(self) -> Path:
        return Path(self.DATA_DIR)


settings = Settings()
