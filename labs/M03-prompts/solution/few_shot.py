"""
M03 Lab — Few-Shot Prompting (Solution)
=========================================
Classify UCC collateral descriptions into categories
using few-shot examples embedded in the prompt.
"""

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-20250514"

# ─── Few-Shot Examples ──────────────────────────────────────────────────────

EXAMPLES = [
    {
        "description": "All accounts receivable and inventory",
        "category": "Blanket Lien",
    },
    {
        "description": "Specific equipment: (2) Caterpillar 320 excavators",
        "category": "Equipment",
    },
    {
        "description": "All crops, livestock, and farm products",
        "category": "Agricultural",
    },
]


def classify_collateral(description: str) -> str:
    """
    Classify a UCC collateral description into a category
    using few-shot prompting.
    """
    # Build the few-shot examples into a prompt
    examples_text = ""
    for ex in EXAMPLES:
        examples_text += f'Description: {ex["description"]}\nCategory: {ex["category"]}\n\n'

    user_message = (
        "Classify the following UCC collateral descriptions into categories. "
        "Here are some examples:\n\n"
        f"{examples_text}"
        f"Now classify this description:\n"
        f"Description: {description}\n"
        f"Category: "
    )

    system_prompt = (
        "You are a UCC filing classification expert. Given a collateral "
        "description from a UCC filing, classify it into the most appropriate "
        "category. Respond with ONLY the category name, nothing else."
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=100,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text.strip()


# ─── Main ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_cases = [
        {
            "description": "All intellectual property, patents, and trademarks",
            "expected": "Intellectual Property / General Intangibles",
        },
        {
            "description": "2021 Peterbilt 579 truck, VIN 1XPBD49X1MD123456",
            "expected": "Specific Equipment / Vehicle",
        },
        {
            "description": "All assets of the Debtor, whether now owned or hereafter acquired",
            "expected": "Blanket Lien",
        },
    ]

    print("=" * 60)
    print("Few-Shot Collateral Classification")
    print("=" * 60)

    for i, case in enumerate(test_cases, 1):
        print(f"\n--- Test {i} ---")
        print(f"Description: {case['description']}")
        print(f"Expected:    {case['expected']}")
        try:
            result = classify_collateral(case["description"])
            print(f"Predicted:   {result}")
            match = "MATCH" if case["expected"].lower() in result.lower() else "CHECK"
            print(f"Status:      [{match}]")
        except Exception as e:
            print(f"[ERROR] {e}")
