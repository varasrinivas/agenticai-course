"""
M22 Lab - Part 2: Benchmark Harness (COMPLETE — run and study)
===============================================================
Measures p50/p95 latency, tokens/sec, and judged quality per model.
Run: python agent_benchmark.py
Output: benchmark_results.csv + benchmark_results.md
"""

import asyncio
import csv
import statistics
import time
from pathlib import Path

import httpx

OLLAMA_URL = "http://localhost:11434/api/generate"
JUDGE_MODEL = "mistral"

# Add competitors after pulling them, e.g. ["phi3:mini", "mistral", "llama3.1:8b"]
MODELS = ["mistral"]

BENCHMARK_PROMPTS = [
    # Entity extraction
    "Extract: debtor=?, secured_party=? from: 'TechCorp Inc granted Wells Fargo a lien on all software assets'",
    "Parse this UCC filing date: 'filed on the fifteenth day of March two thousand twenty-four'",
    "Is 'ACME LLC' and 'Acme Limited Liability Company' the same entity? Answer yes or no with brief reason.",
    # Summarization
    "Summarize in 20 words: Debtor Riverside Corp grants secured party First Bank interest in all machinery and equipment now owned or hereafter acquired.",
    "One-sentence summary: The amendment extends the maturity date of the original UCC-1 financing statement by 5 years from the original lapse date.",
    # Classification
    "Classify as high-risk or low-risk: secured party is a non-bank fintech, collateral is future receivables, filed in a state with no central registry.",
    "Is this a continuation, amendment, or termination? 'The secured party hereby terminates all security interests in the collateral described in the original filing.'",
    # JSON generation
    "Return JSON with keys: entity_type, risk_level, jurisdiction for: 'Delaware LLC with a federal tax lien from IRS'",
    "Generate a JSON summary of: 'UCC-1 #2024-003-456, debtor: Smith Farms LLC, secured party: AgriCredit Corp, collateral: livestock and crops'",
    # Reasoning
    "If a UCC-1 was filed in 2019 and not renewed, is it still valid in 2025? Explain in 2 sentences.",
    "Which takes priority: a UCC-1 filed today or a mortgage filed 3 years ago? Brief answer.",
    # Code assistance
    "Write a one-liner Python to extract all 10-digit UCC filing numbers from a string using regex.",
    # Math/logic
    "A UCC-1 lapses after 5 years. Filed 2020-04-01. Lapse date?",
    "If processing 10,000 filings at 3 seconds each with batch=8, estimate total runtime in hours.",
    # Long context / synthesis
    "Given this partial data: entity_id=E001, name=Acme Corp, address=123 Main St, state=IL, filing_count=3, risk_score=0.72 — generate a brief risk summary.",
    "Compare: debtor_a='First National Leasing LLC' vs debtor_b='1st Natl. Leasing, LLC'. Likely same entity? Confidence?",
    # Edge cases
    "What should an agent do if the Ollama API returns a 503 error mid-response?",
    "An entity resolution agent gets conflicting addresses for the same debtor. What disambiguation strategy minimizes false merges?",
    "List 3 signs that a local LLM agent is suffering from context window overflow.",
]


async def run_single(client: httpx.AsyncClient, model: str, prompt: str) -> dict:
    t0 = time.perf_counter()
    try:
        resp = await client.post(
            OLLAMA_URL,
            json={"model": model, "prompt": prompt, "stream": False,
                  "options": {"num_predict": 300}},
            timeout=180.0,
        )
        resp.raise_for_status()
        data = resp.json()
        elapsed = time.perf_counter() - t0
        eval_count = data.get("eval_count", 1)
        eval_duration_ns = data.get("eval_duration", elapsed * 1e9)
        tps = eval_count / (eval_duration_ns / 1e9) if eval_duration_ns > 0 else 0
        return {"prompt": prompt[:80], "response": data["response"],
                "elapsed_s": elapsed, "tps": tps, "error": None}
    except Exception as e:
        return {"prompt": prompt[:80], "response": "",
                "elapsed_s": time.perf_counter() - t0, "tps": 0, "error": str(e)}


async def score_batch(client: httpx.AsyncClient,
                      prompts_responses: list[tuple[str, str]]) -> list[float]:
    """LLM-as-judge: 1-10 correctness per response (defaults to 5 on failure)."""
    scores = []
    for prompt, response in prompts_responses:
        judge_prompt = (f"Score 1-10 for correctness. Prompt: {prompt[:150]} "
                        f"Response: {response[:250]}\nReply: number only.")
        try:
            r = await client.post(
                OLLAMA_URL,
                json={"model": JUDGE_MODEL, "prompt": judge_prompt,
                      "stream": False, "options": {"num_predict": 5}},
                timeout=60.0,
            )
            score = float(r.json()["response"].strip().split()[0])
            scores.append(min(max(score, 1.0), 10.0))
        except Exception:
            scores.append(5.0)
    return scores


async def benchmark_model(model: str) -> dict:
    print(f"  Benchmarking {model} ({len(BENCHMARK_PROMPTS)} prompts)...")
    async with httpx.AsyncClient() as client:
        results = [await run_single(client, model, p) for p in BENCHMARK_PROMPTS]
        scores = await score_batch(client, [(r["prompt"], r["response"]) for r in results])

    latencies = [r["elapsed_s"] for r in results if r["error"] is None]
    tps_vals = [r["tps"] for r in results if r["tps"] > 0]
    lat_sorted = sorted(latencies)
    return {
        "model": model,
        "n": len(BENCHMARK_PROMPTS),
        "errors": sum(1 for r in results if r["error"]),
        "p50_s": round(statistics.median(latencies), 2) if latencies else 0,
        "p95_s": round(lat_sorted[min(int(len(lat_sorted) * 0.95), len(lat_sorted) - 1)], 2) if latencies else 0,
        "avg_tps": round(statistics.mean(tps_vals), 1) if tps_vals else 0,
        "avg_quality": round(statistics.mean(scores), 1),
    }


def write_csv(results: list[dict], path: str = "benchmark_results.csv") -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)


def write_markdown(results: list[dict], path: str = "benchmark_results.md") -> None:
    lines = ["# Agent Benchmark Results\n",
             "| Model | p50 (s) | p95 (s) | Avg tok/s | Quality/10 | Errors |",
             "|---|---|---|---|---|---|"]
    for r in results:
        lines.append(f"| {r['model']} | {r['p50_s']} | {r['p95_s']} | "
                     f"{r['avg_tps']} | {r['avg_quality']} | {r['errors']} |")
    Path(path).write_text("\n".join(lines), encoding="utf-8")


async def main():
    print(f"Running benchmark across {len(MODELS)} model(s) x {len(BENCHMARK_PROMPTS)} prompts\n")
    results = [await benchmark_model(m) for m in MODELS]
    results.sort(key=lambda x: (-x["avg_quality"], x["p50_s"]))

    print("\n=== Benchmark Results ===")
    print(f"{'Model':<22} {'p50':>6} {'p95':>6} {'tok/s':>7} {'Quality':>9} {'Errors':>7}")
    print("-" * 62)
    for r in results:
        print(f"{r['model']:<22} {r['p50_s']:>6.1f} {r['p95_s']:>6.1f} "
              f"{r['avg_tps']:>7.0f} {r['avg_quality']:>8.1f}/10 {r['errors']:>7}")

    write_csv(results)
    write_markdown(results)
    print("\nSaved: benchmark_results.csv, benchmark_results.md")
    print("Decision rule: pick the SMALLEST model whose quality clears your bar.")


if __name__ == "__main__":
    asyncio.run(main())
