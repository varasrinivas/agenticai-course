"""
M21B Lab: Provider-Agnostic Client Factory
===========================================
One env var (LOCAL_MODEL_PROVIDER) switches every agent in the app
between local Ollama and managed cloud providers.
Run: python local_model_client.py
     LOCAL_MODEL_PROVIDER=groq GROQ_API_KEY=gsk_... python local_model_client.py
"""

import os
from dataclasses import dataclass

from openai import OpenAI


@dataclass
class ProviderConfig:
    """(COMPLETE) Provider-specific settings returned alongside the client."""

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
        """Return a (client, config) tuple for the requested provider.

        TODO:
        1. name = (provider or os.getenv("LOCAL_MODEL_PROVIDER", "ollama")).lower()
        2. If name not in cls.CONFIGS:
             raise ValueError(f"Unknown provider '{name}'. "
                              f"Supported: {', '.join(cls.CONFIGS)}")
        3. cfg = cls.CONFIGS[name]
        4. If name == "ollama":
             base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
             client = OpenAI(base_url=base_url, api_key="ollama")
        5. Else (managed providers):
             key_var = cls.KEY_VARS[name]; api_key = os.environ.get(key_var)
             If not api_key: raise EnvironmentError(f"{key_var} is not set")
               ← name the EXACT env var; missing keys are the #1 deploy failure
             client = OpenAI(base_url=cls.BASE_URLS[name], api_key=api_key)
        6. Return client, cfg
        """
        pass  # Remove this line when you add your code


# ── Example usage (COMPLETE) ──
def run_agent_query(question: str) -> str:
    """Run a simple query against whichever provider is configured."""
    client, cfg = LocalModelClient.create()
    print(f"Provider: {cfg.name}  model: {cfg.default_model}")

    response = client.chat.completions.create(
        model=cfg.default_model,  # never hardcode — names are provider-specific
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Be concise."},
            {"role": "user", "content": question},
        ],
        max_tokens=512,
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    # Sanity checks that don't need any server:
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

    # The real call (needs Ollama, or set LOCAL_MODEL_PROVIDER + key):
    print(f"\nAnswer: {run_agent_query('What is 17 * 23?')}")  # 391
