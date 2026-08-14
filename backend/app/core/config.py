from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # App
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    RESULTS_DIR: str = "/results"
    JOB_TIMEOUT_SECONDS: int = 3600

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:3000"]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://lsap:lsap_secure_pass@postgres:5432/lsap"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Keycloak
    KEYCLOAK_URL: str = "http://keycloak:8080"
    KEYCLOAK_REALM: str = "lsap"
    KEYCLOAK_CLIENT_ID: str = "lsap-frontend"
    KEYCLOAK_CLIENT_SECRET: str = ""

    # Optional pre-seeded keys
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
