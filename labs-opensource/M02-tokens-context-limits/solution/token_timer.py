"""
M02 Lab - Step 3: TokenTimer Benchmark — SOLUTION
==================================================
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
        """Send a chat request and return timing metrics."""
        t_start = time.perf_counter()
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
            )
        except Exception as e:
            raise RuntimeError(
                f"Ollama request failed: {e} (is Ollama running? ollama serve)"
            ) from e

        elapsed = time.perf_counter() - t_start
        usage = response.usage
        content = response.choices[0].message.content or ""

        # decode speed = output tokens / total time
        decode_tps = (usage.completion_tokens / elapsed) if elapsed > 0 else 0

        return TimerResult(
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            elapsed_seconds=elapsed,
            decode_tokens_per_sec=decode_tps,
            content=content,
        )


# ── Benchmark over three prompt sizes ──
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
