"""
M00 Lab - Step 1: Environment Check (COMPLETE — just run it)
=============================================================
Verifies: openai SDK installed, Ollama server reachable, mistral model pulled.
Run: python check_setup.py
"""

import json
import sys
import urllib.request
import urllib.error

OLLAMA_URL = "http://localhost:11434"
REQUIRED_MODEL = "mistral"


def check(label: str, ok: bool, fix: str) -> bool:
    status = "OK " if ok else "FAIL"
    print(f"[{status}] {label}")
    if not ok:
        print(f"       Fix: {fix}")
    return ok


def main() -> None:
    all_ok = True

    # 1. openai SDK importable?
    try:
        import openai
        all_ok &= check(f"openai SDK installed (v{openai.__version__})", True, "")
    except ImportError:
        all_ok &= check("openai SDK installed", False, "pip install openai")

    # 2. Ollama server reachable?
    models = []
    try:
        with urllib.request.urlopen(f"{OLLAMA_URL}/api/tags", timeout=5) as resp:
            data = json.loads(resp.read())
            models = [m["name"] for m in data.get("models", [])]
        all_ok &= check(f"Ollama server reachable at {OLLAMA_URL}", True, "")
    except (urllib.error.URLError, OSError):
        all_ok &= check(
            f"Ollama server reachable at {OLLAMA_URL}", False,
            "Start it with: ollama serve  (or launch the Ollama app)",
        )

    # 3. mistral model pulled?
    has_model = any(m.startswith(REQUIRED_MODEL) for m in models)
    all_ok &= check(
        f"model '{REQUIRED_MODEL}' is pulled ({', '.join(models) or 'none found'})",
        has_model,
        f"ollama pull {REQUIRED_MODEL}",
    )

    print()
    if all_ok:
        print("Environment ready — continue to Step 2 (hello_mistral).")
    else:
        print("Fix the FAIL items above, then re-run this script.")
        sys.exit(1)


if __name__ == "__main__":
    main()
