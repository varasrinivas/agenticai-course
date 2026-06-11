"""
M02 Lab - Step 3: TokenTimer Benchmark
=======================================
Measure your machine's real tokens-per-second with local Mistral.
Run: python token_timer.py
"""

import time
from dataclasses import dataclass
from openai import OpenAI


@dataclass
class TimerResult:
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    elapsed_seconds: float
    decode_tokens_per_sec: float
    content: str


class TokenTimer:
    """Wrap an Ollama call and report latency + throughput metrics."""

    def __init__(self, model: str = "mistral"):
        self.model = model
        self.client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

    def run(self, messages: list[dict], max_tokens: int = 256) -> TimerResult:
        """Send a chat request and return timing metrics.

        TODO:
        1. t_start = time.perf_counter()
        2. Call self.client.chat.completions.create(model=self.model,
           messages=messages, max_tokens=max_tokens)
           — wrap in try/except and raise RuntimeError with a helpful message on failure
        3. elapsed = time.perf_counter() - t_start
        4. usage = response.usage; content = response.choices[0].message.content or ""
        5. decode_tps = usage.completion_tokens / elapsed (guard against elapsed == 0)
        6. Return a TimerResult with all fields filled in
        """
        pass  # Remove this line when you add your code


# ── Benchmark over three prompt sizes (COMPLETE) ──
def make_prompt(approx_tokens: int) -> list[dict]:
    """Generate a padding prompt of approximately the given token count."""
    padding = "benchmark " * (approx_tokens // 2)
    return [
        {"role": "system", "content": "You are a helpful assistant. Answer briefly."},
        {"role": "user", "content": f"Please summarize the following:\n\n{padding}\n\nSummarize in one sentence."},
    ]


def main():
    timer = TokenTimer(model="mistral")

    # Warm-up (avoids model load time polluting benchmarks)
    print("Warming up...")
    _ = timer.run([{"role": "user", "content": "hi"}], max_tokens=5)

    print("\nBenchmark results:")
    print(f"{'Approx Input':>14} {'Prompt Tok':>10} {'Comp Tok':>9} {'Elapsed':>8} {'Decode tok/s':>13}")
    print("-" * 60)

    for target in [100, 500, 1_000]:
        msgs = make_prompt(target)
        result = timer.run(msgs, max_tokens=64)
        print(
            f"{target:>12}-> "
            f"{result.prompt_tokens:>9} "
            f"{result.completion_tokens:>9} "
            f"{result.elapsed_seconds:>7.2f}s "
            f"{result.decode_tokens_per_sec:>12.1f}"
        )


if __name__ == "__main__":
    main()
