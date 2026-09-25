import os
from typing import List
from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = "Cloud-Based Smart Attendance System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    # Database: defaults to SQLite for zero-config local dev;
    # set to PostgreSQL/Supabase URL in production .env
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./attendance.db")

    # Security
    JWT_SECRET: str = os.getenv("JWT_SECRET", "smart_attendance_jwt_secret_dev_key_2026")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Face Recognition Thresholds
    FACE_MATCH_THRESHOLD: float = float(os.getenv("FACE_MATCH_THRESHOLD", "0.48"))
    FLAGGED_REVIEW_THRESHOLD: float = float(os.getenv("FLAGGED_REVIEW_THRESHOLD", "0.60"))
    DEFAULT_PRESENCE_THRESHOLD: float = float(os.getenv("DEFAULT_PRESENCE_THRESHOLD", "75.0"))

    # CORS settings
    CORS_ORIGINS: List[str] = ["*"]


settings = Settings()
