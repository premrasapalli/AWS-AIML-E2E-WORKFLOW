from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "deepseek-r1:7b"
    max_tokens: int = 2048
    temperature: float = 0.7
    timeout_seconds: int = 60
    max_retries: int = 3

    model_config = {"env_prefix": "AIDECOPS_", "env_file": ".env"}


settings = Settings()
