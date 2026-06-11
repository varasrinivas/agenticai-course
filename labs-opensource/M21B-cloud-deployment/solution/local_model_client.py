"""
M21B Lab: Provider-Agnostic Client Factory — SOLUTION
======================================================
Run: python local_model_client.py
"""

import os
from dataclasses import dataclass

from openai import OpenAI


@dataclass
class ProviderConfig:
    """Provider-specific settings returned alongside the client."""

    name: str
    default_model: str
    max_context_tokens: int


class LocalModelClient:
    """Factory for OpenAI-compatible clients across Ollama and managed providers."""

    CONFIGS: dict[str, ProviderConfig] = {
        "ollama": ProviderConfig("ollama", "mistral", 32768),
        "groq": ProviderConfig("groq", "llama-3.3-70b-versatile", 131072),
        "together": ProviderConfig("together", "mistralai/Mistral-7B-Instruct-v0.2", 32768),
        "fireworks": ProviderConfig("fireworks", "accounts/fireworks/models/mistral-7b-instruct", 32768),
    }

    BASE_URLS = {
        "groq": "https://api.groq.com/openai/v1",
        "together": "https://api.together.xyz/v1",
        "fireworks": "https://api.fireworks.ai/inference/v1",
    }

    KEY_VARS = {
        "groq": "GROQ_API_KEY",
        "together": "TOGETHER_API_KEY",
        "fireworks": "FIREWORKS_API_KEY",
    }

    @classmethod
    def create(cls, provider: str | None = None) -> tuple[OpenAI, ProviderConfig]:
        """Return a (client, config) tuple for the requested provider."""
        name = (provider or os.getenv("LOCAL_MODEL_PROVIDER", "ollama")).lower()

        if name not in cls.CONFIGS:
            supported = ", ".join(cls.CONFIGS.keys())
            raise ValueError(f"Unknown provider '{name}'. Supported: {supported}")

        cfg = cls.CONFIGS[name]

        if name == "ollama":
            base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
            client = OpenAI(base_url=base_url, api_key="ollama")
        else:
            key_var = cls.KEY_VARS[name]
            api_key = os.environ.get(key_var)
            if not api_key:
                # Name the EXACT env var — missing keys are the #1 deploy failure
                raise EnvironmentError(f"{key_var} is not set")
            client = OpenAI(base_url=cls.BASE_URLS[name], api_key=api_key)

        return client, cfg


def run_agent_query(question: str) -> str:
    """Run a simple query against whichever provider is configured."""
    client, cfg = LocalModelClient.create()
    print(f"Provider: {cfg.name}  model: {cfg.default_model}")

    response = client.chat.completions.create(
        model=cfg.default_model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Be concise."},
            {"role": "user", "content": question},
        ],
        max_tokens=512,
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    try:
        LocalModelClient.create("nonexistent")
        raise AssertionError("unknown provider was accepted!")
    except ValueError as e:
        print(f"Unknown-provider check OK: {e}")

    try:
        os.environ.pop("GROQ_API_KEY", None)
        LocalModelClient.create("groq")
        raise AssertionError("groq without key was accepted!")
    except EnvironmentError as e:
        print(f"Missing-key check OK: {e}")

    print(f"\nAnswer: {run_agent_query('What is 17 * 23?')}")  # 391
