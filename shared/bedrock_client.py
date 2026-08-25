import json
import os
import httpx
import boto3
from botocore.config import Config
from typing import Optional
from .config import settings


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

MODEL_ALIASES = {
    "ollama": "qwen3:0.6b",
    "ollama-deepseek": "deepseek-r1:7b",
    "ollama-llama3": "llama3.2:1b",
    "ollama-mistral": "mistral:latest",
    "ollama-qwen": "qwen3:latest",
    "nova-lite": "us.amazon.nova-lite-v1:0",
    "nova-pro": "us.amazon.nova-pro-v1:0",
    "nova-premier": "us.amazon.nova-premier-v1:0",
    "titan-express": "amazon.titan-text-express-v1",
    "titan-lite": "amazon.titan-text-lite-v1",
    "titan-premier": "amazon.titan-text-premier-v1:0",
}

MODEL_MAX_TOKENS = {
    "qwen3:0.6b": 2048,
    "deepseek-r1:7b": 8192,
    "llama3.2:1b": 4096,
    "mistral:latest": 8192,
    "qwen3:latest": 8192,
    "us.amazon.nova-lite-v1:0": 5120,
    "us.amazon.nova-pro-v1:0": 5120,
    "us.amazon.nova-premier-v1:0": 5120,
    "amazon.titan-text-express-v1": 8192,
    "amazon.titan-text-lite-v1": 4096,
    "amazon.titan-text-premier-v1:0": 32768,
}

OLLAMA_MODELS = {"qwen3:0.6b", "deepseek-r1:7b", "llama3.2:1b", "mistral:latest", "qwen3:latest"}


class BedrockClient:
    def __init__(
        self,
        region_name: Optional[str] = None,
        model_alias: Optional[str] = None,
    ):
        self.region_name = region_name or settings.aws_region
        self.model_alias = model_alias or "ollama"
        self.model_id = MODEL_ALIASES.get(self.model_alias, settings.bedrock_model_id)
        self.max_tokens = min(
            settings.max_tokens, MODEL_MAX_TOKENS.get(self.model_id, 4096)
        )
        self.temperature = settings.temperature

        self.use_ollama = self.model_id in OLLAMA_MODELS

        if not self.use_ollama:
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
        if self.use_ollama:
            return self._invoke_ollama(prompt, system_prompt, max_tokens, temperature)
        elif "nova" in self.model_id.lower():
            return self._invoke_nova(prompt, system_prompt, max_tokens, temperature)
        else:
            return self._invoke_titan(prompt, system_prompt, max_tokens, temperature)

    def _invoke_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": self.model_id,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens or self.max_tokens,
                        "temperature": temperature or self.temperature,
                        "top_p": 0.9,
                    },
                },
            )
            response.raise_for_status()
            result = response.json()
            return result["message"]["content"]

    def _invoke_nova(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        messages = [{"role": "user", "content": [{"text": prompt}]}]
        system = []
        if system_prompt:
            system.append({"text": system_prompt})

        body = json.dumps({
            "messages": messages,
            "system": system,
            "inferenceConfig": {
                "maxTokens": max_tokens or self.max_tokens,
                "temperature": temperature or self.temperature,
                "topP": 0.9,
            },
        })

        response = self.client.invoke_model(
            body=body,
            contentType="application/json",
            accept="application/json",
            modelId=self.model_id,
        )

        result = json.loads(response["body"].read())
        return result["output"]["message"]["content"][0]["text"]

    def _invoke_titan(
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

        body = json.dumps({
            "inputText": full_prompt,
            "textGenerationConfig": {
                "maxTokenCount": max_tokens or self.max_tokens,
                "temperature": temperature or self.temperature,
                "topP": 0.9,
            },
        })

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
        return list(MODEL_ALIASES.keys())
