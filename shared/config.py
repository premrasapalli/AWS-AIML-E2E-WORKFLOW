from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "amazon.titan-text-express-v1"
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout_seconds: int = 60
    max_retries: int = 3

    model_config = {"env_prefix": "AIDECOPS_", "env_file": ".env"}


settings = Settings()
