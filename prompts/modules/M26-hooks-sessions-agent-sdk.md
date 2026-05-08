# M26: Build with the Agent SDK — Hooks, Sessions & Declarative Agents

**Track**: 9 — Cert Prep | **Position**: 26 of 30 | **Level**: Advanced
**Prerequisites**: M05, M12, M15B, M25
**Estimated Time**: 90-120 minutes
**Track Color**: var(--track-certprep) / #D4A843

## Why This Module Must Exist
M15B taught students to build agents using the raw `client.messages.create()` loop — manually checking `stop_reason`, executing tools, appending messages, and managing the conversation. That's the "from scratch" approach. But Anthropic's Agent SDK provides a declarative, higher-level way to build agents where the SDK manages the loop for you.

Students need to:
1. Build the SAME UCC agent using the Agent SDK
2. Compare raw loop vs SDK (when to use which)
3. Learn hooks (PreToolUse, PostToolUse) for guardrails and logging
4. Understand sessions for multi-turn persistence
5. See how the Agent SDK maps to cert exam concepts

## Module Structure

### Section 1: Raw Loop vs Agent SDK — Why Both Exist

**The comparison the student needs to see:**

```
RAW LOOP (M15B approach):                 AGENT SDK approach:
──────────────────────                    ──────────────────────
YOU write the while loop                  SDK runs the loop for you
YOU check stop_reason                     SDK handles stop_reason
YOU execute tools                         SDK calls your tool functions
YOU append messages                       SDK manages conversation
YOU handle errors in the loop             SDK has built-in error handling
YOU implement retry logic                 SDK has configurable retries
YOU add logging manually                  Hooks give you logging points
YOU manage context window                 SDK manages context

~60 lines of loop code                    ~15 lines of agent definition
Full control                              Less control, more guardrails
Best for: custom loop logic               Best for: standard agent patterns
```

**When to use which:**
- **Raw loop**: When you need custom control flow (non-standard tool execution, custom retry patterns, streaming mid-loop, parallel tool calls with custom aggregation)
- **Agent SDK**: When you want standard agent patterns fast (tool execution, guardrails via hooks, session management, production-ready error handling)

### Section 2: Build the UCC Agent with Agent SDK (Hands-On Lab)

Rebuild the EXACT same UCC filing research agent from M15B, but using the Agent SDK.

**Step 1: Setup (5 min)**
```bash
pip install anthropic
export ANTHROPIC_API_KEY=your-key-here
```

**Step 2: Define the tools as Python functions (10 min)**

Instead of JSON Schema tool definitions, the Agent SDK uses decorated Python functions:

```python
# tools.py — Same tools as M15B but as decorated functions
import anthropic

agent = anthropic.Agent(
    model="claude-sonnet-4-20250514",
    system="You are a UCC filing research agent. Search thoroughly for name variations."
)

@agent.tool
def search_filings(debtor_name: str, state: str = None) -> list[dict]:
    """Search UCC filings by debtor name. Supports partial matching."""
    # Same mock data search from M15B
    from mock_data import FILINGS_DB
    results = []
    for f in FILINGS_DB:
        if debtor_name.upper() in f["debtor_name"].upper():
            if state is None or f["state"] == state:
                results.append(f)
    return results

@agent.tool
def get_filing_details(filing_number: str) -> dict:
    """Get full details for a specific UCC filing."""
    from mock_data import FILINGS_DB
    for f in FILINGS_DB:
        if f["filing_number"] == filing_number:
            return f
    return {"error": f"Filing {filing_number} not found"}

@agent.tool
def calculate_risk_score(entity_id: str) -> dict:
    """Calculate risk score based on filing patterns."""
    # Same risk calculation from M15B
    return {"entity_id": entity_id, "risk_score": 0.73, "risk_level": "HIGH"}
```

Run: verify tools load — `python -c "from tools import agent; print(f'{len(agent.tools)} tools registered')"`
Expected: `3 tools registered`
Checkpoint: Tools defined as decorated functions

**Step 3: Run the agent (5 min)**

```python
# run_agent.py — The entire agent in 5 lines
from tools import agent

response = agent.run("What is the total lien exposure for Acme Corporation?")
print(response)
```

Run: `python run_agent.py`
Expected: Agent searches, finds variations, calculates risk, returns narrative response
Checkpoint: Same quality output as M15B's 60-line raw loop — in 5 lines

**Step 4: Compare side-by-side (5 min)**

```
M15B Raw Loop:                          M26 Agent SDK:
─────────────                           ──────────────
import anthropic                        import anthropic
client = anthropic.Anthropic()          agent = anthropic.Agent(...)
tools = [{...json schema...}]           @agent.tool
messages = [...]                        def search_filings(...):
while True:                                 ...
    response = client.messages.create(  @agent.tool
        model=...,                      def get_filing_details(...):
        tools=tools,                        ...
        messages=messages               response = agent.run(question)
    )
    if response.stop_reason == "end_turn":
        break
    for block in response.content:
        if block.type == "tool_use":
            result = execute_tool(...)
            messages.append(...)
            messages.append(...)

~60 lines                               ~25 lines
```

### Section 3: Hooks — Guardrails at Every Step

Hooks let you intercept the agent at specific points WITHOUT modifying the core loop.

**PreToolUse Hook**: Runs BEFORE a tool is called
- Use for: input validation, PII redaction, rate limiting, logging
- Can BLOCK the tool call (return deny)

**PostToolUse Hook**: Runs AFTER a tool returns
- Use for: output validation, result caching, compliance logging
- Can MODIFY the result before Claude sees it

**Step 5: Add a PreToolUse hook for logging (10 min)**

```python
# hooks_agent.py
import anthropic
from datetime import datetime

agent = anthropic.Agent(
    model="claude-sonnet-4-20250514",
    system="You are a UCC filing research agent."
)

@agent.hook("pre_tool_use")
def log_tool_call(tool_name: str, tool_input: dict):
    """Log every tool call before execution."""
    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] TOOL CALL: {tool_name}({tool_input})")
    return True  # True = allow, False = block

@agent.hook("post_tool_use")
def log_tool_result(tool_name: str, tool_input: dict, tool_result):
    """Log every tool result after execution."""
    timestamp = datetime.now().isoformat()
    result_preview = str(tool_result)[:100]
    print(f"[{timestamp}] TOOL RESULT: {tool_name} → {result_preview}...")
    return tool_result  # Return result unchanged (or modify it)

# Register same tools as before
@agent.tool
def search_filings(debtor_name: str, state: str = None) -> list[dict]:
    """Search UCC filings by debtor name."""
    from mock_data import FILINGS_DB
    return [f for f in FILINGS_DB if debtor_name.upper() in f["debtor_name"].upper()]

# ... other tools ...

response = agent.run("Find all filings for Acme Corporation")
print("\n=== RESPONSE ===\n")
print(response)
```

Run: `python hooks_agent.py`
Expected:
```
[2025-03-15T10:23:01] TOOL CALL: search_filings({"debtor_name": "Acme Corporation"})
[2025-03-15T10:23:01] TOOL RESULT: search_filings → [{"filing_number": "NY-2024-001"...
[2025-03-15T10:23:02] TOOL CALL: search_filings({"debtor_name": "ACME CORP"})
[2025-03-15T10:23:02] TOOL RESULT: search_filings → [{"filing_number": "CA-2024-001"...
...
=== RESPONSE ===
[narrative report]
```
Checkpoint: Every tool call logged with timestamp — zero changes to the agent logic

**Step 6: Add a PreToolUse hook that BLOCKS dangerous calls (10 min)**

```python
@agent.hook("pre_tool_use")
def block_dangerous_calls(tool_name: str, tool_input: dict):
    """Block search_filings calls with suspiciously broad queries."""
    if tool_name == "search_filings":
        query = tool_input.get("debtor_name", "")
        if len(query) < 3:
            print(f"BLOCKED: Query too broad: '{query}'")
            return False  # Block this call
    return True  # Allow
```

Run with a question that triggers a broad search
Checkpoint: Agent tries to search with a 1-2 character query and gets blocked

**Step 7: Add a PostToolUse hook that redacts PII (10 min)**

```python
@agent.hook("post_tool_use")
def redact_pii(tool_name: str, tool_input: dict, tool_result):
    """Redact SSNs and phone numbers from tool results before Claude sees them."""
    import re
    result_str = str(tool_result)
    result_str = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN REDACTED]', result_str)
    result_str = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE REDACTED]', result_str)
    return eval(result_str) if isinstance(tool_result, (list, dict)) else result_str
```

Checkpoint: PII never reaches Claude — redacted at the hook level

### Section 4: Sessions — Multi-Turn Persistence

**Step 8: Add session support for follow-up questions (15 min)**

```python
# session_agent.py
import anthropic

agent = anthropic.Agent(
    model="claude-sonnet-4-20250514",
    system="You are a UCC filing research agent."
)

# ... register tools ...

# Create a persistent session
session = agent.create_session()

# Turn 1
response1 = session.send("What is the lien exposure for Acme Corporation?")
print("Turn 1:", response1)

# Turn 2 — follow-up (session remembers Turn 1)
response2 = session.send("What about their Texas filings specifically?")
print("Turn 2:", response2)

# Turn 3 — another follow-up
response3 = session.send("If they file a continuation on the CA filing, how would that change the risk?")
print("Turn 3:", response3)

# Fork a session (create a branch for what-if analysis)
what_if_session = session.fork()
response4 = what_if_session.send("What if they also terminate the NY filing?")
print("What-if:", response4)

# Original session is unaffected by the fork
response5 = session.send("Summarize everything we discussed")
print("Summary:", response5)  # Does NOT include the what-if branch
```

Checkpoint: Follow-ups work without resending full history. Fork creates independent branch.

### Section 5: Putting It All Together — Production Agent with SDK (15 min)

**Step 9: Complete production agent**

Combine: Agent SDK + hooks (logging + PII redaction + blocking) + session + the ML delinquency model from the prelude as a tool.

```python
# production_agent.py
import anthropic

agent = anthropic.Agent(
    model="claude-sonnet-4-20250514",
    system="You are a credit risk analyst agent with access to UCC filings and a delinquency ML model."
)

# Hooks
@agent.hook("pre_tool_use")
def guardrails(tool_name, tool_input):
    # Log + block broad queries + rate limit
    ...

@agent.hook("post_tool_use")
def compliance(tool_name, tool_input, tool_result):
    # Redact PII + audit log + cache results
    ...

# Tools (including ML model from prelude)
@agent.tool
def search_filings(...): ...

@agent.tool
def predict_delinquency(...): ...

@agent.tool
def get_filing_details(...): ...

# Run with session
session = agent.create_session()
response = session.send("Assess the delinquency risk for Acme Corporation")
```

### Section 6: Raw Loop vs Agent SDK Decision Guide

| Factor | Use Raw Loop | Use Agent SDK |
|---|---|---|
| Custom loop control | ✅ | ❌ |
| Standard patterns | ❌ overkill | ✅ |
| Guardrails via hooks | Write manually | ✅ built-in |
| Session management | Write manually | ✅ built-in |
| Streaming mid-loop | ✅ full control | Limited |
| Parallel tool calls | ✅ custom aggregation | SDK-managed |
| Learning/understanding | ✅ see everything | Abstracts away |
| Production speed | Slower to build | ✅ faster |
| Cert exam | Must understand | Must understand |

"Learn the raw loop first (M15B) so you understand what's happening. Use the Agent SDK (M26) when building for production."

## Quiz Focus (7 questions)
1. What does the Agent SDK handle that the raw loop does not? (loop management, stop_reason, message appending)
2. What does a PreToolUse hook return to block a call? (False)
3. Can a PostToolUse hook modify the tool result? (Yes — return the modified result)
4. What is session.fork() for? (Create an independent branch for what-if analysis)
5. When should you use the raw loop instead of the SDK? (Custom control flow, non-standard patterns)
6. Hooks run inside or outside the agent loop? (Inside — they intercept each tool call)
7. Does the Agent SDK replace the need to understand the raw loop? (No — the raw loop teaches what the SDK abstracts)

## Animation Requirements
1. **Raw loop vs SDK comparison** — side-by-side animation showing the same agent running, left side shows every step explicitly, right side shows SDK handling it
2. **Hook lifecycle** — animated flow: message arrives → PreToolUse fires → tool executes → PostToolUse fires → result returns to Claude
3. **Session forking** — tree diagram showing conversation branching at the fork point
4. **Production agent stack** — layered diagram: tools at bottom → SDK loop → hooks → session → FastAPI wrapper
