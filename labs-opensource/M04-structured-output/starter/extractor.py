"""
M04 Lab - Step 2: Extract with Forced Tool Use + Validation
============================================================
Force Mistral to call extract_contact, validate the args with Pydantic.
Run: python extractor.py
"""

import json

from openai import OpenAI
from pydantic import ValidationError
from schema_and_data import ContactInfo, TEST_SIGNATURES

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

# Tool definition: the Pydantic schema becomes the parameters (COMPLETE)
EXTRACT_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_contact",
        "description": "Extract structured contact information from an email signature.",
        "parameters": ContactInfo.model_json_schema(),
    },
}


def extract_contact(text: str) -> ContactInfo:
    """Extract contact info using forced tool use + Pydantic validation.

    TODO:
    1. Call client.chat.completions.create() with:
       - model="mistral"
       - tools=[EXTRACT_TOOL]
       - tool_choice={"type": "function", "function": {"name": "extract_contact"}}
         ← this FORCES the model to call the tool
       - messages=[{"role": "user", "content": f"Extract contact info:\\n\\n{text}"}]
    2. tool_calls = response.choices[0].message.tool_calls
       If empty/None → raise ValueError("Model did not call the tool")
    3. args = json.loads(tool_calls[0].function.arguments)   # JSON STRING → dict
    4. return ContactInfo(**args)   # raises ValidationError if schema violated
    """
    pass  # Remove this line when you add your code


# ── Scoreboard over all 5 test signatures (COMPLETE) ──
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
