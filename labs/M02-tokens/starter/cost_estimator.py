"""
M02 Lab — Step 2: Cost Estimator
==================================
Predict API costs before making requests.
"""

# Pricing per million tokens (as of 2024)
PRICING = {
    "claude-haiku": {"input": 0.25, "output": 1.25},
    "claude-sonnet": {"input": 3.00, "output": 15.00},
    "claude-opus": {"input": 15.00, "output": 75.00},
}

def estimate_cost(input_tokens: int, output_tokens: int, model: str = "claude-sonnet") -> dict:
    """
    Estimate the cost of an API call.
    Returns dict with input_cost, output_cost, total_cost, model.
    """
    # TODO:
    # 1. Look up the model's pricing from PRICING dict
    # 2. Calculate input_cost = (input_tokens / 1_000_000) * price_per_million_input
    # 3. Calculate output_cost = (output_tokens / 1_000_000) * price_per_million_output
    # 4. Return {"input_cost": ..., "output_cost": ..., "total_cost": ..., "model": model}
    pass

if __name__ == "__main__":
    print("=== Cost Estimator ===\n")
    scenarios = [
        ("Short query", 100, 200),
        ("Medium query", 1000, 2000),
        ("Batch of 1000", 1000 * 1000, 1000 * 2000),
    ]
    for model_key in ["claude-haiku", "claude-sonnet"]:
        print(f"Model: {model_key}")
        for label, inp, out in scenarios:
            try:
                est = estimate_cost(inp, out, model_key)
                print(f"  {label:<18} ({inp} in / {out} out):   ${est['total_cost']:.6f}")
            except Exception as e:
                print(f"  {label:<18} [ERROR] {e}")
        print()
    # Cost comparison
    try:
        haiku = estimate_cost(1000, 2000, "claude-haiku")
        sonnet = estimate_cost(1000, 2000, "claude-sonnet")
        ratio = sonnet["total_cost"] / haiku["total_cost"]
        print("Cost comparison:")
        print(f"  Sonnet is {ratio:.1f}x more expensive than Haiku for the same workload.")
        daily_haiku = haiku["total_cost"] * 10000
        daily_sonnet = sonnet["total_cost"] * 10000
        print(f"  For 10,000 queries/day, Haiku = ${daily_haiku:.2f}/day, Sonnet = ${daily_sonnet:.2f}/day.")
    except Exception as e:
        print(f"  [ERROR] {e}")
