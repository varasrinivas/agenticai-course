"""
M21B Lab: Connection Verifier (COMPLETE — just run it)
=======================================================
Works identically against local Ollama, an SSH-tunneled cloud VM, or a
managed endpoint — that's the whole point of the OpenAI-compatible pattern.
Run: python verify_connection.py
     OLLAMA_BASE_URL=http://localhost:11434/v1 python verify_connection.py
"""

import os

from openai import OpenAI


def verify_connection(base_url: str | None = None) -> None:
    """Verify Ollama (or any compatible endpoint) is reachable."""
    url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")

    client = OpenAI(base_url=url, api_key=os.getenv("API_KEY", "ollama"))

    try:
        response = client.chat.completions.create(
            model=os.getenv("MODEL", "mistral"),
            messages=[{"role": "user", "content": "Reply with the single word: connected"}],
            max_tokens=10,
        )
        reply = (response.choices[0].message.content or "").strip()
        print(f"[OK] Endpoint {url} responded: {reply!r}")
        print(f"     Model: {response.model}")
        print(f"     Tokens used: {response.usage.total_tokens}")
    except Exception as exc:
        print(f"[FAIL] Cannot reach endpoint at {url}: {exc}")
        print("       Local:  is Ollama running? (ollama serve)")
        print("       Cloud:  is the SSH tunnel up?")
        print("       Command: gcloud compute ssh ollama-server -- -L 11434:localhost:11434 -N -f")
        raise SystemExit(1)


if __name__ == "__main__":
    verify_connection()
