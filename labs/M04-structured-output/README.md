# M04: Structured Output & Parsing -- Lab

## What You'll Build

In this lab you will build a **Structured Data Extraction Pipeline** that parses freetext UCC filing descriptions and extracts machine-readable structured data. By the end, you will know three progressively more reliable techniques for getting structured output from Claude: prompt-based JSON extraction, tool_use for guaranteed structure, and schema validation with Pydantic (Python) or Zod (Node.js).

You will work through three exercises:

| Exercise | File | What You'll Learn |
|----------|------|-------------------|
| **JSON Extraction with Prompting** | `json_extractor` | How to prompt Claude to return valid JSON and parse the response |
| **Tool Use for Guaranteed Structure** | `tool_extractor` | How tool_use forces Claude to return data matching a JSON Schema |
| **Validation with Pydantic/Zod** | `validated_extractor` | How to validate extracted data for semantic correctness, not just syntax |

---

## Prerequisites

- **M01-M03** completed (LLM basics, API calls, prompt engineering)
- **Python 3.10+** or **Node.js 18+**
- An **Anthropic API key** (set as `ANTHROPIC_API_KEY` in a `.env` file or environment variable)
- Install dependencies:

```bash
# Python
pip install anthropic python-dotenv pydantic

# Node.js
npm install @anthropic-ai/sdk dotenv zod
```

---

## Lab Steps

### Step 1: JSON Extraction with Prompting

Prompt engineering is the simplest way to get JSON from Claude. You craft a system prompt that instructs Claude to return ONLY valid JSON, then parse the response with `json.loads` (Python) or `JSON.parse` (Node.js).

**Run the starter:**

```bash
cd starter

# Python
python json_extractor.py

# Node.js
node json_extractor.js
```

**Your task:** Open `starter/json_extractor.py` (or `.js`) and complete the `extract_filing_json` function:

1. Build a system prompt that tells Claude to extract UCC filing data from freetext and return ONLY valid JSON (no markdown, no explanation)
2. Define the expected fields: `filing_type`, `filing_date`, `debtor_name`, `debtor_type`, `debtor_state`, `secured_party`, `collateral_type`, `collateral_description`
3. Call the API with the freetext as the user message
4. Parse the JSON response and return the resulting dict/object

**Expected output:** Each of the 3 sample filings should produce a JSON object with all 8 fields populated. For example, the first filing should extract `filing_type: "UCC-1"`, `debtor_name: "Greenfield Logistics LLC"`, etc.

**Checkpoint:** Your function should handle all 3 samples without throwing parse errors. If you get `JSONDecodeError`, check that your system prompt says "return ONLY valid JSON" and does not allow markdown code fences.

**Troubleshooting:**
- If Claude wraps JSON in ```json blocks, add "Do not use markdown code fences" to your system prompt
- If fields are missing, list all 8 expected fields explicitly in the prompt
- If you get rate-limited, add a small delay between calls

---

### Step 2: Tool Use for Guaranteed Structure

Prompt-based extraction can fail -- Claude might add commentary, use wrong field names, or return malformed JSON. Tool use solves this by defining a JSON Schema that Claude MUST conform to when "calling" the tool.

**Run the starter:**

```bash
cd starter

# Python
python tool_extractor.py

# Node.js
node tool_extractor.js
```

**Your task:** Open `starter/tool_extractor.py` (or `.js`) and complete the `extract_with_tool_use` function:

1. The tool definition `extract_filing_data` is already provided with the full JSON Schema
2. Call `client.messages.create` with the tool definition and `tool_choice={"type": "tool", "name": "extract_filing_data"}` to force Claude to use the tool
3. Find the `tool_use` content block in the response
4. Return the `input` field from that block -- this is your guaranteed-structure JSON

**Expected output:** The same 3 filings should produce identical field names every time. The key difference from Step 1: tool_use output is ALWAYS valid JSON matching the schema.

**Checkpoint:** Every response must contain a `tool_use` content block. If you get a `text` block instead, make sure you set `tool_choice` to force tool use.

**Troubleshooting:**
- If `tool_use` block is missing, verify `tool_choice` is set (not just `tools`)
- If field values differ from Step 1, that is expected -- the structure is guaranteed, not the interpretation
- The `collateral_type` field should be one of: "Blanket Lien", "Equipment", "Accounts Receivable", "Inventory", "Intellectual Property", "Real Property", "Agricultural", "Medical Equipment", "Other"

---

### Step 3: Validation with Pydantic/Zod

Guaranteed JSON structure is not enough. The data inside could still be wrong -- a date could be "yesterday", a filing type could be "UCC-99". Schema validation catches these semantic errors.

**Run the starter:**

```bash
cd starter

# Python
python validated_extractor.py

# Node.js
node validated_extractor.js
```

**Your task:** Open `starter/validated_extractor.py` (or `.js`) and complete the `extract_and_validate` function:

1. Use the tool_use extraction from Step 2 to get raw structured data
2. Pass it through the Pydantic model `UCCFiling` (Python) or Zod schema `uccFilingSchema` (Node.js)
3. Handle validation errors gracefully -- catch `ValidationError` and return a meaningful error message
4. Test with both valid filings AND the deliberately malformed edge case

**Expected output:** The 3 valid filings should pass validation. The edge case input should trigger a validation error (missing required fields, invalid filing type, etc.).

**Checkpoint:** You should see both successful validations AND at least one `ValidationError` from the edge case. If all inputs pass, your validators are too lenient.

**Troubleshooting:**
- If Pydantic is not installed: `pip install pydantic`
- If Zod is not installed: `npm install zod`
- If the edge case passes validation, tighten your validators (e.g., filing_type must be exactly "UCC-1" or "UCC-3")
- If valid filings fail, check that your date validator accepts "YYYY-MM-DD" format

---

## Final Verification

You have completed the lab when:

- [ ] `json_extractor` extracts JSON from all 3 freetext descriptions without parse errors
- [ ] `tool_extractor` returns structured data with guaranteed field names using tool_use
- [ ] `validated_extractor` passes valid filings and rejects the malformed edge case
- [ ] You can explain WHY tool_use is more reliable than prompt-based JSON extraction
- [ ] You understand the difference between structural validation (JSON Schema) and semantic validation (Pydantic/Zod)

---

## What You Built

You built a three-layer structured data extraction pipeline:

- **Prompt-based extraction** -- the simplest approach, works 90%+ of the time but can fail on edge cases
- **Tool use extraction** -- guarantees valid JSON structure by forcing Claude to conform to a JSON Schema
- **Validated extraction** -- catches semantic errors (wrong dates, invalid enum values) that structural validation misses

This layered approach (extract -> structure -> validate) is the foundation of every production agent that processes unstructured data. You will use these patterns in the capstone projects (Domain A healthcare pre-auth, Domain C UCC data engineering) and throughout the rest of the course.

---

## Next

Continue to **[M05: Function Calling & Tool Use](../../output/M05-function-calling.html)** to learn how to give Claude the ability to call external functions and APIs.
