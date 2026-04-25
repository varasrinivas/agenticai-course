"""
M03 Lab — Message Roles (Solution)
====================================
Explore how system prompts, user messages, and assistant prefill
change Claude's responses to the same question.
"""

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-20250514"


def basic_call(user_message: str) -> str:
    """Send a simple user message with no system prompt."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def with_system_prompt(system: str, user_message: str) -> str:
    """Send a user message with a system prompt that sets Claude's role."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text


def with_prefill(system: str, user_message: str, assistant_prefill: str) -> str:
    """Use assistant prefill to guide the response format."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system,
        messages=[
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": assistant_prefill},
        ],
    )
    return assistant_prefill + response.content[0].text


# ─── Main ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    question = "What is a UCC-1 filing?"

    system_prompt = (
        "You are a UCC filing expert. You specialize in Uniform Commercial Code "
        "filings, secured transactions, and lien searches. Provide accurate, "
        "concise explanations using proper legal terminology while remaining "
        "accessible to non-lawyers."
    )

    prefill = "## Analysis\n"

    # --- Call 1: Basic (no system prompt) ---
    print("=" * 60)
    print("CALL 1: Basic — No System Prompt")
    print("=" * 60)
    try:
        result = basic_call(question)
        print(result)
    except Exception as e:
        print(f"[ERROR] {e}")

    # --- Call 2: With system prompt ---
    print("\n" + "=" * 60)
    print("CALL 2: With System Prompt (UCC Expert)")
    print("=" * 60)
    try:
        result = with_system_prompt(system_prompt, question)
        print(result)
    except Exception as e:
        print(f"[ERROR] {e}")

    # --- Call 3: With system prompt + prefill ---
    print("\n" + "=" * 60)
    print("CALL 3: With System Prompt + Assistant Prefill")
    print("=" * 60)
    try:
        result = with_prefill(system_prompt, question, prefill)
        print(result)
    except Exception as e:
        print(f"[ERROR] {e}")
