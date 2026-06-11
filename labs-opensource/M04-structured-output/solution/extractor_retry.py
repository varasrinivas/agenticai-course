"""
M04 Lab - Step 3: Retry with Error Feedback — SOLUTION
=======================================================
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
    """Extract with automatic retry on validation failure."""
    last_error = None

    for attempt in range(1, max_retries + 1):
        prompt = f"Extract contact info:\n\n{text}"
        if last_error:
            # Feed the model its own failure — this is what makes it self-correct
            prompt += f"\n\nPrevious attempt failed with: {last_error}"
            prompt += "\nFix the output to match the required schema exactly."

        try:
            response = client.chat.completions.create(
                model="mistral",
                tools=[EXTRACT_TOOL],
                tool_choice={"type": "function", "function": {"name": "extract_contact"}},
                messages=[{"role": "user", "content": prompt}],
            )
            tool_calls = response.choices[0].message.tool_calls
            if not tool_calls:
                raise ValueError("Model did not call the tool")

            args = json.loads(tool_calls[0].function.arguments)
            contact = ContactInfo(**args)
            print(f"  Attempt {attempt}: Success!")
            return contact

        except ValidationError as e:
            last_error = str(e)
            print(f"  Attempt {attempt}: Validation error, retrying...")
            time.sleep(2 ** attempt)  # exponential backoff
        except Exception as e:
            last_error = str(e)
            print(f"  Attempt {attempt}: Error — {e}")
            time.sleep(2 ** attempt)

    raise RuntimeError(f"Failed after {max_retries} attempts: {last_error}")


if __name__ == "__main__":
    tricky = "Contact: J. at some-company, email is j (at) co (dot) com, phone TBD"
    print(f"Input: {tricky}\n")
    try:
        result = extract_with_retry(tricky)
        print(f"\nExtracted: {result.name} <{result.email}>")
    except RuntimeError as e:
        print(f"\nGave up: {e}")
        print("(That can legitimately happen — the input is designed to be hostile.)")
