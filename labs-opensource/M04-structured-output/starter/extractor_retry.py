"""
M04 Lab - Step 3: Retry with Error Feedback
============================================
When validation fails, tell the model WHAT failed and let it self-correct.
Run: python extractor_retry.py
"""

import json
import time

from openai import OpenAI
from pydantic import ValidationError
from schema_and_data import ContactInfo

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

EXTRACT_TOOL = {
    "type": "function",
    "function": {
        "name": "extract_contact",
        "description": "Extract contact info. ALL fields must be valid (email must be a real address format).",
        "parameters": ContactInfo.model_json_schema(),
    },
}


def extract_with_retry(text: str, max_retries: int = 3) -> ContactInfo:
    """Extract with automatic retry on validation failure.

    TODO:
    last_error = None
    For attempt in 1..max_retries:
      1. prompt = f"Extract contact info:\\n\\n{text}"
         If last_error: append
           f"\\n\\nPrevious attempt failed with: {last_error}\\n"
           "Fix the output to match the required schema exactly."
      2. Call the API (same forced tool_choice pattern as Step 2),
         parse tool_calls[0].function.arguments with json.loads
      3. return ContactInfo(**args) on success
      4. except ValidationError as e:
           last_error = str(e); print attempt status; time.sleep(2 ** attempt)
         except Exception as e (API/JSON errors):
           last_error = str(e); print attempt status; time.sleep(2 ** attempt)
    After the loop: raise RuntimeError(f"Failed after {max_retries} attempts: {last_error}")
    """
    pass  # Remove this line when you add your code


# ── Test with a deliberately tricky signature (COMPLETE) ──
if __name__ == "__main__":
    tricky = "Contact: J. at some-company, email is j (at) co (dot) com, phone TBD"
    print(f"Input: {tricky}\n")
    try:
        result = extract_with_retry(tricky)
        print(f"\nExtracted: {result.name} <{result.email}>")
    except RuntimeError as e:
        print(f"\nGave up: {e}")
        print("(That can legitimately happen — the input is designed to be hostile.)")
