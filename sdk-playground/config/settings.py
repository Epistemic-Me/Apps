from pydantic_settings import BaseSettings
from typing import Dict, Optional
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings."""
    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Dialectic Dashboard"
    DEBUG: bool = False
    
    # DeepEval Settings
    DEEPEVAL_API_KEY: Optional[str] = None
    EVALUATION_BATCH_SIZE: int = 10
    
    # Database Settings
    DATABASE_URL: str = "sqlite:///./dialectic.db"
    
    # Metrics Settings
    METRICS_WINDOW_SIZE: int = 100  # Number of interactions to consider for metrics
    ENTROPY_THRESHOLD: float = 0.7  # Threshold for high entropy warning
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Returns cached settings instance."""
    return Settings() 