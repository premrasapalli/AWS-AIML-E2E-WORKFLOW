import json
import boto3
from botocore.config import Config
from typing import Optional
from .config import settings


TITAN_MODELS = {
    "titan-express": "amazon.titan-text-express-v1",
    "titan-lite": "amazon.titan-text-lite-v1",
    "titan-premier": "amazon.titan-text-premier-v1:0",
}

MODEL_MAX_TOKENS = {
    "amazon.titan-text-express-v1": 8192,
    "amazon.titan-text-lite-v1": 4096,
    "amazon.titan-text-premier-v1:0": 32768,
}


class BedrockClient:
    def __init__(
        self,
        region_name: Optional[str] = None,
        model_alias: Optional[str] = None,
    ):
        self.region_name = region_name or settings.aws_region
        self.model_id = TITAN_MODELS.get(
            model_alias or "titan-express", settings.bedrock_model_id
        )
        self.max_tokens = min(
            settings.max_tokens, MODEL_MAX_TOKENS.get(self.model_id, 8192)
        )
        self.temperature = settings.temperature

        self.client = boto3.client(
            "bedrock-runtime",
            region_name=self.region_name,
            config=Config(
                connect_timeout=settings.timeout_seconds,
                read_timeout=settings.timeout_seconds,
                retries={"max_attempts": settings.max_retries, "mode": "adaptive"},
            ),
        )

    def invoke(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        if system_prompt:
            full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
        else:
            full_prompt = prompt

        body = json.dumps(
            {
                "inputText": full_prompt,
                "textGenerationConfig": {
                    "maxTokenCount": max_tokens or self.max_tokens,
                    "temperature": temperature or self.temperature,
                    "topP": 0.9,
                },
            }
        )

        response = self.client.invoke_model(
            body=body,
            contentType="application/json",
            accept="application/json",
            modelId=self.model_id,
        )

        result = json.loads(response["body"].read())
        return result["results"][0]["outputText"]

    def invoke_with_retry(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> str:
        return self.invoke(prompt, system_prompt=system_prompt, **kwargs)

    @property
    def available_models(self) -> list[str]:
        return list(TITAN_MODELS.keys())
