# M04 Lab: Structured Output

> Free-form text is for humans; agents need JSON. You'll force Mistral to return schema-shaped data via a tool call, validate it with Pydantic/Zod, and add retry-with-feedback for when validation fails.

## Prerequisites

- M01 complete
- Dependencies:
  ```bash
  pip install openai "pydantic>=2.0"     # Python
  npm install openai zod                 # Node.js
  ```

## Exercises

| Step | File | What You Build | Key Concept |
|------|------|---------------|-------------|
| 1 | `schema_and_data.py` / `.js` | (Complete — just run) | Pydantic/Zod schema + 5 test signatures |
| 2 | `extractor.py` / `.js` | Forced tool call + validation | `tool_choice`, `tool_calls`, schema validation |
| 3 | `extractor_retry.py` / `.js` | Retry with error feedback | Self-correcting extraction |

## The Core Trick

Instead of asking for JSON in prose (and praying), you define a **tool** whose parameters ARE your schema, then **force** the model to call it:

```python
tools = [{
    "type": "function",
    "function": {
        "name": "extract_contact",
        "description": "Extract structured contact information from an email signature.",
        "parameters": ContactInfo.model_json_schema(),   # Pydantic generates the JSON Schema
    },
}]

response = client.chat.completions.create(
    model="mistral",
    tools=tools,
    tool_choice={"type": "function", "function": {"name": "extract_contact"}},  # FORCED
    messages=[...],
)
args = json.loads(response.choices[0].message.tool_calls[0].function.arguments)
contact = ContactInfo(**args)   # Pydantic validates — raises ValidationError if wrong
```

> **Heads-up if you compared with the course HTML:** the OpenAI format wraps tool definitions in `{"type": "function", "function": {...}}`, forces with `tool_choice={"type": "function", "function": {"name": ...}}`, and returns results in `message.tool_calls[0].function.arguments` (a JSON **string**). There is no `input_schema` / `response.content` block — that's the Anthropic SDK shape.

## Step 1: Inspect the Schema and Test Data

**File:** `starter/schema_and_data.py` (or `.js`) — complete; run it to see the generated JSON Schema and the 5 test signatures (easy → hard: pipes, accents, nicknames, multi-line).

## Step 2: Extract with Forced Tool Use + Validation

**File:** `starter/extractor.py` (or `.js`)

Implement `extract_contact(text)` using the pattern above, then run it against all 5 test signatures and print a ✓/✗ scoreboard.

**Expect 4–5 of 5 to pass** with Mistral-7B. Signature 4 ("Alex K. | Product @ StartupXYZ") sometimes confuses role/company — that's your motivation for Step 3.

## Step 3: Retry with Error Feedback

**File:** `starter/extractor_retry.py` (or `.js`)

Implement `extract_with_retry(text, max_retries=3)`:
1. Try the extraction
2. On `ValidationError` (or missing tool call): **append the error message to the prompt** ("Previous attempt failed with: ... Fix the output.") and try again
3. Back off exponentially (`2 ** attempt` seconds) between attempts
4. After `max_retries`, raise

Test it on the deliberately tricky signature `"Contact: J. at some-company, email is j (at) co (dot) com, phone TBD"` — watch the model fix its own output when told exactly what was wrong (the email field usually fails Zod's `.email()` check on attempt 1).

## Verify Everything Works

```bash
python starter/schema_and_data.py && python starter/extractor.py && python starter/extractor_retry.py
```

## Stretch Goals

- Add a `confidence: float` field to the schema and a `0.0-1.0` description — does Mistral fill it sensibly?
- Batch-extract all 5 signatures in ONE call by making the tool accept an array of contacts
