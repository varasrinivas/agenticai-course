#!/usr/bin/env python3
"""
M03B Lab: diagnose.py (COMPLETE — runs against YOUR context_budget.py)
========================================================================
Demonstrates the poisoned-transcript effect and the fix.
Run: python diagnose.py
"""

import json
import time

from openai import OpenAI
from context_budget import ContextBudget, summarize_history

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")


def ask_model(budget: ContextBudget) -> tuple[str, dict]:
    system, messages = budget.build_messages()
    t0 = time.time()
    try:
        response = client.chat.completions.create(
            model="mistral",
            messages=[{"role": "system", "content": system}] + messages,
            max_tokens=300,
        )
        answer = response.choices[0].message.content or ""
        usage = {
            "input_tokens": response.usage.prompt_tokens,
            "output_tokens": response.usage.completion_tokens,
            "latency_s": round(time.time() - t0, 2),
        }
    except Exception as e:
        answer, usage = f"[error: {e}]", {"input_tokens": 0, "output_tokens": 0, "latency_s": 0}
    return answer, usage


def main():
    with open("poisoned_transcript.json", encoding="utf-8") as f:
        fixture = json.load(f)

    base_args = dict(
        model="mistral",
        system_prompt=fixture["system_prompt"],
        tool_definitions=fixture["tool_definitions"],
        history=fixture["history"],
        current_user_message=fixture["current_user_message"],
    )

    # --- Run 1: rotted context ---
    rotted = ContextBudget(**base_args)
    breakdown = rotted.account()
    print("=== Token Breakdown (rotted) ===")
    for layer, tok in breakdown.items():
        print(f"  {layer:15s}: {tok:,} tokens")
    print(f"  {'TOTAL':15s}: {rotted.total():,} / {rotted.max_tokens:,}  strategy={rotted.strategy()!r}")

    print("\n>>> Run 1: ROTTED context (no fix)")
    answer_a, usage_a = ask_model(rotted)
    print(f"Tokens: {usage_a['input_tokens']} in, {usage_a['output_tokens']} out  ({usage_a['latency_s']}s)")
    print(f"Answer: {answer_a}\n")

    # --- Run 2: after checkpoint ---
    fixed = ContextBudget(**base_args)
    fixed.history = summarize_history(fixed.history, keep_recent=4)
    print(">>> Run 2: COMPRESSED context (after checkpoint)")
    print(f"  Total after compression: {fixed.total():,} tokens  strategy={fixed.strategy()!r}")
    answer_b, usage_b = ask_model(fixed)
    print(f"Tokens: {usage_b['input_tokens']} in, {usage_b['output_tokens']} out  ({usage_b['latency_s']}s)")
    print(f"Answer: {answer_b}\n")

    print("=" * 60)
    print(f"Token delta:   {usage_a['input_tokens'] - usage_b['input_tokens']:+,} input tokens")
    print(f"Latency delta: {usage_a['latency_s'] - usage_b['latency_s']:+.2f}s")
    print("\nSuccess check: Run 2 must still cite ORD-88421 and November 3rd.")


if __name__ == "__main__":
    main()
