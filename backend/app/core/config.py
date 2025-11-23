from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    app_name: str = "MedFin"
    api_version: str = "v1"
    database_url: Optional[str] = "sqlite+aiosqlite:///./medfin.db"
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Healthcare cost estimation defaults
    default_coverage_percentage: float = 0.80
    default_deductible: float = 2000.0
    default_out_of_pocket_max: float = 8000.0
    
    # Financial assistance thresholds
    low_income_threshold: float = 40000.0  # Annual income
    medium_income_threshold: float = 80000.0
    
    class Config:
        env_file = ".env"


settings = Settings()

