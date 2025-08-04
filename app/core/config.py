from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # --- Project ---
    PROJECT_NAME: str = "TB-API-SKD"
    VERSION: str = "0.1.0"
    DEBUG: bool = False  # Security: Never enable in production

    # --- ThingsBoard Connection ---
    TB_HOST: AnyHttpUrl = "http://localhost"
    TB_USERNAME: str = ""
    TB_PASSWORD: str = ""

    # --- API Security ---
    API_KEY: str = ""  # Optional API key for endpoint protection
    ACCESS_TOKEN: str | None = None  # Populated after auth if not pre-set
    SECRET_KEY: str = ""  # For JWT/session signing if needed
    
    # --- Network Security ---
    ALLOWED_HOSTS: List[str] = []  # Prevent Host header attacks
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] | List[str] = []
    
    # --- Rate Limiting ---
    RATE_LIMIT_REQUESTS: int = 100  # Requests per minute
    RATE_LIMIT_WINDOW: int = 60     # Window in seconds

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i]
        return v

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_hosts(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i]
        return v

    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings() 