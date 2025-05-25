from pydantic import BaseSettings
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default_secret_key")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/event_management")
    
    # Add this to handle SSL requirements
    @property
    def DATABASE_URL_WITH_SSL(self):
        if self.DATABASE_URL.startswith("postgresql"):
            return self.DATABASE_URL + "?sslmode=require"
        return self.DATABASE_URL

settings = Settings()