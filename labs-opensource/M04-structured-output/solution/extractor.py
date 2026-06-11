"""
M04 Lab - Step 2: Extract with Forced Tool Use + Validation — SOLUTION
=======================================================================
Run: python extractor.py
"""

import json

from openai import OpenAI
from pydantic import ValidationError
from schema_and_data import ContactInfo, TEST_SIGNATURES

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

EXTRACT_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_contact",
        "description": "Extract structured contact information from an email signature.",
        "parameters": ContactInfo.model_json_schema(),
    },
}


def extract_contact(text: str) -> ContactInfo:
    """Extract contact info using forced tool use + Pydantic validation."""
    response = client.chat.completions.create(
        model="mistral",
        tools=[EXTRACT_TOOL],
        # Forcing the tool guarantees structured output instead of prose
        tool_choice={"type": "function", "function": {"name": "extract_contact"}},
        messages=[{"role": "user", "content": f"Extract contact info:\n\n{text}"}],
    )

    tool_calls = response.choices[0].message.tool_calls
    if not tool_calls:
        raise ValueError("Model did not call the tool")

    # arguments is a JSON string — parse it, then validate with Pydantic
    args = json.loads(tool_calls[0].function.arguments)
    return ContactInfo(**args)


if __name__ == "__main__":
    successes = 0
    for i, sig in enumerate(TEST_SIGNATURES, 1):
        try:
            contact = extract_contact(sig)
            print(f"[OK]   Sig {i}: {contact.name} <{contact.email}> @ {contact.company or 'N/A'}")
            successes += 1
        except (ValidationError, ValueError) as e:
            print(f"[FAIL] Sig {i}: {str(e)[:100]}")
        except Exception as e:
            print(f"[FAIL] Sig {i}: API error — {e}")

    print(f"\nResults: {successes}/{len(TEST_SIGNATURES)} extracted successfully")
