from pydantic_settings import BaseSettings
from typing import Optional
from urllib.parse import quote_plus
import os


class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "computing_power"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    
    WORK_HOUR_START: int = 9
    WORK_HOUR_END: int = 18
    
    HIGH_USAGE_THRESHOLD: float = 60.0
    LOW_USAGE_THRESHOLD: float = 30.0
    
    @property
    def DATABASE_URL(self) -> str:
        encoded_password = quote_plus(self.DB_PASSWORD)
        return f"postgresql://{self.DB_USER}:{encoded_password}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        extra = "ignore"


settings = Settings()
