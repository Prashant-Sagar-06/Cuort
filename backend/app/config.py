import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "Cuort"
    APP_ENV: str = "development"

    # Groq API
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "openai/gpt-oss-120b"

    # PostgreSQL + pgvector
    DATABASE_URL: str = "postgresql+psycopg://cuort:cuort_secret_password@localhost:5432/cuort_db"

    # Security & JWT
    JWT_SECRET_KEY: str = "change_me_to_a_long_random_secret_32_bytes_min"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Embeddings
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    model_config = SettingsConfigDict(
        env_file=(BASE_DIR / ".env", Path(".env")),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
