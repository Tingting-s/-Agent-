from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Settings(BaseModel):
    app_name: str = Field(default=os.getenv("APP_NAME", "multi-tool-agent-office-assistant"))
    app_env: str = Field(default=os.getenv("APP_ENV", "development"))
    debug: bool = Field(default=os.getenv("DEBUG", "true").lower() == "true")
    host: str = Field(default=os.getenv("HOST", "127.0.0.1"))
    port: int = Field(default=int(os.getenv("PORT", "8000")))
    api_prefix: str = Field(default=os.getenv("API_PREFIX", ""))
    log_level: str = Field(default=os.getenv("LOG_LEVEL", "INFO"))
    DASHSCOPE_API_KEY: str = Field(default=os.getenv("DASHSCOPE_API_KEY", ""))
    DASHSCOPE_BASE_URL: str = Field(
        default=os.getenv(
            "DASHSCOPE_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
    )
    QWEN_MODEL: str = Field(default=os.getenv("QWEN_MODEL", "qwen3.5-plus"))
    LLM_TIMEOUT: int = Field(default=int(os.getenv("LLM_TIMEOUT", "30")))


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
