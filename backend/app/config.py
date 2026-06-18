from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/cyber_audit"

    # JWT
    SECRET_KEY: str = "change-this-to-a-secure-256-bit-key-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # File Storage
    STORAGE_PATH: str = "/storage/reports"
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt"]
    MAX_FILE_SIZE_MB: int = 50

    # MinIO Storage
    MINIO_URL: str = "http://localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "cyber-audit-reports"

    # File Encryption
    FILE_ENCRYPTION_KEY: str = "MTIzNDU2Nzg5MDEyMzQ1Njc4OTAxMjM0NTY3ODkwMTI="

    # ClamAV Integration
    CLAMAV_HOST: str = "clamav"
    CLAMAV_PORT: int = 3310

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    # Admin defaults
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "Admin@123"
    DEFAULT_ADMIN_EMAIL: str = "admin@cyberaudit.local"

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
    }


settings = Settings()
