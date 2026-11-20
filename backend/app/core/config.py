import os
from pathlib import Path
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator

# Locate backend/.env regardless of current working directory
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE) if _ENV_FILE.exists() else ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_ENV: str = Field(default="development")
    APP_NAME: str = Field(default="NEXORA AI")
    APP_DEBUG: bool = Field(default=True)
    API_V1_STR: str = Field(default="/api/v1")
    SECRET_KEY: str = Field(default="development-secret-key-change-in-production-32bytes-minimum")

    SERVER_HOST: str = Field(default="127.0.0.1")
    SERVER_PORT: int = Field(default=8000)
    ALLOWED_ORIGINS: Union[str, List[str]] = Field(default="http://localhost:3000,http://127.0.0.1:3000")

    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)
    JWT_ALGORITHM: str = Field(default="HS256")

    # Argon2id Parameters (RFC 9106 recommended profile)
    ARGON2_TIME_COST: int = Field(default=2)        # 2 iterations
    ARGON2_MEMORY_COST: int = Field(default=65536)  # 64 MB RAM
    ARGON2_PARALLELISM: int = Field(default=4)      # 4 parallel threads
    ARGON2_HASH_LEN: int = Field(default=32)        # 32 bytes output length
    ARGON2_SALT_LEN: int = Field(default=16)        # 16 bytes salt length

    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./nexora_dev.db")

    AI_PROVIDER: str = Field(default="local")
    GEMINI_API_KEY: str = Field(default="")
    AI_TIMEOUT_SECONDS: int = Field(default=10)

    # Sandbox Configuration: MUST BE 'container_isolated' for executing untrusted user code
    # 'disabled' explicitly disables arbitrary execution when no secure container runtime is live
    SANDBOX_MODE: str = Field(default="disabled")
    SANDBOX_TIMEOUT_SECONDS: int = Field(default=5)
    SANDBOX_MEMORY_LIMIT_MB: int = Field(default=128)
    SANDBOX_MAX_OUTPUT_BYTES: int = Field(default=65536)

    @field_validator("ALLOWED_ORIGINS")
    @classmethod
    def parse_allowed_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

settings = Settings()
