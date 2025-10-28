from __future__ import annotations

from pathlib import Path
import os
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv


class TavilyConfig(BaseModel):
    api_key: Optional[str] = None
    max_results: int = 10
    search_depth: str = "advanced"
    include_domains: List[str] = Field(default_factory=list)
    exclude_domains: List[str] = Field(default_factory=list)
    timeout: int = 30
    max_retries: int = 3


class OpenAIConfig(BaseModel):
    api_key: Optional[str] = None
    model: str = "gpt-4-turbo-preview"
    temperature: float = 0.3
    max_tokens: int = 4096
    timeout: int = 60
    max_retries: int = 3
    fallback_model: str = "gpt-3.5-turbo"


class RateLimitingConfig(BaseModel):
    tavily_rpm: int = 60
    openai_rpm: int = 3500
    openai_tpm: int = 90000


class CostLimitsConfig(BaseModel):
    daily_budget: float = 10.0
    per_request_max: float = 0.5
    alert_threshold: float = 8.0


class APIConfig(BaseModel):
    tavily: TavilyConfig = TavilyConfig()
    openai: OpenAIConfig = OpenAIConfig()
    rate_limiting: RateLimitingConfig = RateLimitingConfig()
    cost_limits: CostLimitsConfig = CostLimitsConfig()


class AppSettings(BaseSettings):
    api: APIConfig = APIConfig()

    model_config = SettingsConfigDict(env_nested_delimiter="__", env_prefix="DATAFORGE__", extra="ignore")

    @staticmethod
    def load_from_yaml(config_path: Path) -> "AppSettings":
        # Load .env first
        load_dotenv()
        # Expand environment variables inside YAML by preprocessing text
        with config_path.open("r", encoding="utf-8") as f:
            raw = f.read()
        expanded = os.path.expandvars(raw)
        data = yaml.safe_load(expanded) or {}
        return AppSettings(**data)


_settings: Optional[AppSettings] = None


def get_settings(config_path: Optional[str | Path] = None) -> AppSettings:
    global _settings
    if _settings is not None:
        return _settings

    path = Path(config_path) if config_path else Path("config.yaml")
    _settings = AppSettings.load_from_yaml(path)
    return _settings
