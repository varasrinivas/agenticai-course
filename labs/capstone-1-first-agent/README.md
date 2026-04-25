# Capstone 1: First Agent -- Single-Tool Conversational Assistant

## What You'll Build

In this capstone you will build your first complete AI agent: a conversational assistant that uses a single tool to look up real-world data and respond in natural language. The agent runs in a terminal loop -- you type a question, the agent decides whether it needs to call a tool, executes the tool, and then responds with a helpful answer.

You will pick **one** of three industry domains:

| Domain | Agent | Tool |
|---|---|---|
| **A -- Healthcare** | Pre-Auth Status Checker | `get_preauth_status(reference_id)` |
| **B -- Ecommerce** | B2B Order Status Bot | `get_order_status(po_number)` |
| **C -- UCC Filings** | UCC Filing Lookup Agent | `search_ucc_filings(business_name, state)` |

All three domains follow the same architecture. The only difference is the data and the tool schema.

**Difficulty:** 1 out of 5 stars -- Beginner

**Skills practiced:**
- Tool use basics (M05)
- Conversation management (M08)
- Structured output (M04)

---

## Prerequisites

- Modules M01 through M08 completed
- Python 3.10+ installed (`python --version`)
- Node.js 18+ installed (optional, for the JS solution) (`node --version`)
- Anthropic API key set as an environment variable:

```bash
# Linux / macOS
export ANTHROPIC_API_KEY="sk-ant-..."

# Windows PowerShell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

- Anthropic Python SDK installed:

```bash
pip install anthropic
```

- (Optional) Anthropic Node.js SDK installed:

```bash
npm install @anthropic-ai/sdk
```

---

## Setup

1. Navigate to the capstone directory:

```bash
cd labs/capstone-1-first-agent
```

2. Pick a domain folder:

```bash
cd domain-a-healthcare   # or domain-b-ecommerce or domain-c-ucc
```

3. Start with the `starter/` folder. When you get stuck, peek at `solution/`. When you want to verify your output, compare against `expected_output/sample_output.txt`.

---

## Lab Instructions -- Domain A: Healthcare Pre-Auth Status Checker

### Step 1: Understand the Mock Data

**What:** Open `starter/mock_data.py` and read through the pre-authorization records.

**Why:** Your agent's tool will look up records from this dictionary. Understanding the data shape tells you what fields your tool will return.

**Run:**

```bash
python -c "from mock_data import PREAUTH_RECORDS; import json; print(json.dumps(list(PREAUTH_RECORDS.keys()), indent=2))"
```

**Expected output:** A list of 10 reference IDs like `PA-2024-00142`.

**Checkpoint:** Can you describe what fields each record contains?

---

### Step 2: Implement the Tool Function

**What:** Open `starter/tools.py`. Fill in the `get_preauth_status` function body so it looks up a reference ID in `PREAUTH_RECORDS` and returns the matching record (or an error message if not found).

**Why:** This is the function Claude will call when it decides it needs to look up a pre-auth. The tool definition (schema) is already written -- you just need the implementation.

**Run:**

```bash
python -c "from tools import get_preauth_status; import json; print(json.dumps(get_preauth_status('PA-2024-00142'), indent=2))"
```

**Expected output:** A JSON object with the record's status, patient info, CPT code, and reviewer notes.

**Checkpoint:** Does your function return a clear error message for an invalid reference ID like `PA-0000-XXXXX`?

**Troubleshooting:**
- `KeyError` -- make sure you handle missing keys with `.get()` or an `if` check.
- Import error -- make sure `mock_data.py` is in the same directory.

---

### Step 3: Wire Up the Agent Loop

**What:** Open `starter/agent.py`. Fill in the three TODOs:
1. Send the user's message to Claude with the tool definition
2. Check if Claude's response has a `tool_use` stop reason and extract the tool call
3. Execute the tool, send the result back to Claude, and get the final response

**Why:** This is the core agent loop: User -> Claude -> Tool -> Claude -> User. Every agent you build in this course will follow this pattern.

**Run:**

```bash
python agent.py
```

Then type: `What is the status of pre-auth PA-2024-00142?`

**Expected output:** The agent responds with the status and next steps in natural language (see `expected_output/sample_output.txt`).

**Checkpoint:** Try asking about a reference ID that does not exist. Does the agent handle it gracefully?

**Troubleshooting:**
- `AuthenticationError` -- check that `ANTHROPIC_API_KEY` is set.
- `Tool not found` -- make sure you pass the tool schema in `tools` parameter of `client.messages.create()`.
- Agent echoes raw JSON -- make sure you send the tool result back to Claude and return Claude's *second* response to the user.

---

### Step 4: Test Edge Cases

**What:** Try these queries and verify the agent handles each one correctly:

1. A valid pre-auth: `Check PA-2024-00142`
2. An invalid reference: `Look up PA-9999-99999`
3. A conversational message with no lookup needed: `Hi, who are you?`
4. A pre-auth that was denied: `What happened with PA-2024-00398?`

**Why:** A production agent must handle happy paths, sad paths, and off-topic messages.

**Checkpoint:** The agent should never crash. It should respond helpfully even when the tool returns an error.

---

## Lab Instructions -- Domain B: B2B Ecommerce Order Status Bot

### Step 1: Understand the Mock Data

**What:** Open `starter/mock_data.py` and review the order records.

**Run:**

```bash
python -c "from mock_data import ORDER_RECORDS; import json; print(json.dumps(list(ORDER_RECORDS.keys()), indent=2))"
```

**Checkpoint:** Can you identify orders in different statuses (shipped, processing, backordered)?

---

### Step 2: Implement the Tool Function

**What:** Fill in `get_order_status` in `starter/tools.py`.

**Run:**

```bash
python -c "from tools import get_order_status; import json; print(json.dumps(get_order_status('PO-2024-8847'), indent=2))"
```

**Checkpoint:** Does it return a clear error for invalid PO numbers?

---

### Step 3: Wire Up the Agent Loop

**What:** Fill in the three TODOs in `starter/agent.py` (same pattern as Domain A).

**Run:**

```bash
python agent.py
```

Then type: `Where is my order PO-2024-8847?`

**Checkpoint:** The agent returns a natural language summary of the order status.

---

### Step 4: Test Edge Cases

Try: valid PO, invalid PO, conversational message, backordered order.

---

## Lab Instructions -- Domain C: UCC Filing Lookup Agent

### Step 1: Understand the Mock Data

**What:** Open `starter/mock_data.py` and review the UCC filing records.

**Run:**

```bash
python -c "from mock_data import UCC_FILINGS; import json; print(json.dumps(list(UCC_FILINGS.keys()), indent=2))"
```

**Checkpoint:** Can you identify filings in different states (active, lapsed, amended)?

---

### Step 2: Implement the Tool Function

**What:** Fill in `search_ucc_filings` in `starter/tools.py`.

**Run:**

```bash
python -c "from tools import search_ucc_filings; import json; print(json.dumps(search_ucc_filings('Meridian', 'DE'), indent=2))"
```

**Checkpoint:** Does it handle partial name matches? Does it filter by state correctly?

---

### Step 3: Wire Up the Agent Loop

**What:** Fill in the three TODOs in `starter/agent.py` (same pattern as Domains A and B).

**Run:**

```bash
python agent.py
```

Then type: `Search for UCC filings for Meridian in Delaware`

**Checkpoint:** The agent returns a natural language summary of matching filings.

---

### Step 4: Test Edge Cases

Try: valid business name, no results, conversational message, multiple matches.

---

## Final Verification

When you have completed your chosen domain, run through this checklist:

- [ ] Agent starts without errors
- [ ] Agent calls the tool when given a valid lookup query
- [ ] Agent returns a natural language response (not raw JSON)
- [ ] Agent handles invalid/missing IDs gracefully
- [ ] Agent responds to conversational messages without calling the tool
- [ ] Agent can handle multiple queries in a single session (conversation loop)
- [ ] Your output matches the samples in `expected_output/sample_output.txt`

---

## What You Built

Congratulations! You built a complete single-tool conversational agent. Here is what you practiced:

- **Tool definitions** -- you wrote an Anthropic-format tool schema with name, description, and input_schema
- **Agent loop** -- you implemented the User -> Claude -> Tool -> Claude -> User cycle
- **Conversation state** -- you maintained a message history across multiple turns
- **Error handling** -- your agent handles missing records and unexpected input without crashing
- **Natural language responses** -- Claude interprets raw tool output and explains it in plain English

---

## What's Next

In **Capstone 2: Multi-Tool Orchestrator**, you will add multiple tools to a single agent and let Claude decide which tool to call (and when to call more than one). You will also add guardrails and input validation.
