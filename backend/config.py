"""
config.py — Academic-System central configuration

All environment variables are read here using pydantic-settings.
One place for all configurations = easy to maintain and secure (no hardcode).
"""

from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """
    The class settings are automatically read from the .env file in the project root.
    Each field here equals one line in .env.
    """
    
    # APP
    APP_NAME: str = "Academic System"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # DATABASE (POSTGRESQL)
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "academic_system"
    DB_USER : str = "postgres"
    DB_PASSWORD: str = "adin123"
    
    @property
    def DATABASE_URL(self) -> str:
        """
        Assembles a PostgreSQL connection string from its components.
        Format: postgresql://user:password@host:port/dbname
        """
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )
    
    # JWT AUTH
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 8
    
    # GROQ
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    
    # RAG / Vector DB
    CHROMA_DB_PATH:  str = "./chroma_db"
    RAG_CSV_PATH: str = "/.backend/data/academic_guidelines"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    # COMPUTER VISION
    FACE_TOLERANCE: float = 0.5
    LIVENESS_THRESHOLD: float = 0.45 # Best 0.7 for production
    
    # CAMPUS LOCATION
    CAMPUS_LATITUDE: float = -2.964177
    CAMPUS_LONGITUDE: float = 104.726011
    CAMPUS_RADIUS_METER: float = 300.0
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

@lru_cache()
def get_settings() -> Settings:
    """
    Singleton settings — read once, cached forever.
    Use lru_cache to prevent rereading .env on every request.

    How to use it in another file:
    from backend.config import get_settings
    settings = get_settings()
    """
    return Settings()