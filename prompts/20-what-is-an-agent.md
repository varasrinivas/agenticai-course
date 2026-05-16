# What Is and Isn't an Agent — The Clear Boundary

Add to M00 AFTER the prelude and business case, BEFORE the existing "What Is an Agent" section. This replaces vague definitions with a concrete, hands-on comparison.

## The Confusion

Students hear "agent" and think any code that calls an LLM is an agent. It's not. There are THREE distinct levels:

```
Level 1: LLM CALL        — your code asks, LLM answers, done
Level 2: LLM WORKFLOW    — your code orchestrates multiple LLM calls in a fixed sequence
Level 3: LLM AGENT       — LLM decides what to do next, your code provides the tools
```

The CRITICAL difference: WHO makes the decisions?
- Level 1-2: YOUR CODE decides everything (what to call, in what order, when to stop)
- Level 3: The LLM decides (what tool to call, what to search next, when it has enough info)

## Level 1: LLM Call (NOT an agent)

```python
# level1_llm_call.py — Just calling Claude
import anthropic
client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Summarize this UCC filing: " + filing_text}]
)

print(response.content[0].text)
# Done. One call. One response. YOUR code decided to summarize.
```

What this IS:
- A single API call
- YOUR code decides what to ask
- Claude responds, program ends
- No tools, no loop, no decisions by Claude

Real-world examples of Level 1:
- Chatbot that answers questions
- Text summarizer
- Code reviewer that reads code and gives feedback
- Email draft generator
- Translation service

## Level 2: LLM Workflow (NOT an agent)

```python
# level2_workflow.py — Fixed sequence of LLM calls
import anthropic
client = anthropic.Anthropic()

# Step 1: Extract entities (YOUR code decided to do this first)
extract = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Extract debtor name and secured party from: " + filing_text}]
)
entities = extract.content[0].text

# Step 2: Classify risk (YOUR code decided this is step 2)
classify = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": f"Classify risk level for these entities: {entities}"}]
)
risk = classify.content[0].text

# Step 3: Generate report (YOUR code decided this is the final step)
report = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=2048,
    messages=[{"role": "user", "content": f"Write a risk report. Entities: {entities}. Risk: {risk}"}]
)

print(report.content[0].text)
# Done. Three calls. Fixed order. YOUR code decided every step.
```

What this IS:
- Multiple LLM calls in sequence
- YOUR code decides the order (always extract → classify → report)
- Each step's output feeds the next
- No branching, no tool use, no decisions by Claude
- If step 1 finds no entities, step 2 still runs (YOUR code doesn't adapt)

Real-world examples of Level 2:
- ETL pipeline: extract → transform → load (each step uses LLM)
- Content pipeline: research → draft → edit → publish
- Data processing: parse → validate → enrich → store
- CI/CD: analyze code → generate tests → review tests

The key tell: if you draw the workflow as a flowchart, every path is known BEFORE runtime. There are no decision diamonds where Claude chooses the path.

## Level 3: Agent (THIS is an agent)

```python
# level3_agent.py — Claude decides what to do
import anthropic
client = anthropic.Anthropic()

tools = [
    {"name": "search_filings", "description": "Search UCC filings by name", ...},
    {"name": "get_details", "description": "Get filing details", ...},
    {"name": "calculate_risk", "description": "Calculate risk score", ...}
]

messages = [{"role": "user", "content": "What is the lien exposure for Acme Corporation?"}]

while True:
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        tools=tools,
        messages=messages
    )
    
    if response.stop_reason == "end_turn":
        print(response.content[0].text)
        break  # Claude decided it has enough info
    
    # Claude decided which tool to call — not your code
    for block in response.content:
        if block.type == "tool_use":
            result = execute_tool(block.name, block.input)
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": block.id, "content": str(result)}
            ]})
    # Loop back — Claude decides what's next
```

What this IS:
- A loop where CLAUDE decides what happens
- Claude picks which tool to call (not hardcoded)
- Claude decides when to call another tool or stop
- Claude discovers things at runtime (name variations, missing data)
- The execution path is UNKNOWN before runtime

What makes it an agent — the THREE requirements:
1. TOOLS: Claude can take actions (search, calculate, fetch)
2. LOOP: Claude can call tools multiple times
3. DECISIONS: Claude chooses what to do based on results

Remove any one and it's not an agent:
- Tools but no loop → Level 1 (single tool call, still your code decides)
- Loop but no tools → chatbot (multi-turn conversation, no actions)
- Tools + loop but your code decides → Level 2 (workflow with tool steps)

## The Decision Matrix

| Question | Level 1: LLM Call | Level 2: Workflow | Level 3: Agent |
|---|---|---|---|
| How many LLM calls? | 1 | 2+ (fixed count) | Unknown (dynamic) |
| Who decides the sequence? | YOUR code | YOUR code | CLAUDE |
| Can it use tools? | No | No (or fixed tools in fixed order) | Yes (Claude picks) |
| Does it loop? | No | No (linear pipeline) | Yes (until done) |
| Can it adapt to results? | No | No | Yes |
| Execution path known upfront? | Yes | Yes | No |
| stop_reason checked? | No | No | Yes (tool_use vs end_turn) |

## The Litmus Test

Ask yourself: "If I remove the LLM and replace it with a hardcoded response, does the program still work the same way?"

- Level 1: Yes — replace Claude with a canned summary, program works identically
- Level 2: Yes — replace each Claude call with a canned output, pipeline works identically
- Level 3: NO — the agent's behavior depends on Claude's DECISIONS about what to search, what tool to call, when to stop. A canned response can't make those decisions.

If you can replace the LLM with hardcoded responses and the program works the same → it's NOT an agent.

## Hands-On: Build All Three (20 minutes)

### Step 1: Level 1 — LLM Call (3 min)
Create `level1_call.py` with the single-call example above.
Run: `python level1_call.py`
Expected: A summary of the filing. One call, done.
Observe: no tools, no loop, no decisions.

### Step 2: Level 2 — Workflow (5 min)
Create `level2_workflow.py` with the 3-step pipeline above.
Run: `python level2_workflow.py`
Expected: Extract → Classify → Report. Three calls, fixed order.
Observe: YOUR code decided every step. Try removing step 2 — the program breaks because step 3 expects classification input. The pipeline is rigid.

### Step 3: Level 3 — Agent (7 min)
Create `level3_agent.py` with the agent loop above.
Run: `python level3_agent.py "What is the lien exposure for Acme Corporation?"`
Expected: Claude searches → finds variations → calculates → reports. 4-6 calls, dynamic.
Observe: YOU didn't tell Claude to search for name variations. Claude DECIDED to. That decision is what makes it an agent.

### Step 4: The Proof (5 min)
Run the agent with a DIFFERENT question: 
`python level3_agent.py "Which states have the most UCC filings?"`
Expected: Claude calls DIFFERENT tools in a DIFFERENT order. The code didn't change — Claude's DECISIONS changed.

Now try changing the question in Level 2. The pipeline still runs extract → classify → report regardless of the question. It can't adapt.

THAT is the difference.

## Where This Fits in the Course

```
M00: You learn the boundary (this section)
M01-M04: You build Level 1 (LLM calls)
M05: You add tools — first step toward Level 3
M12: You add the loop — now it's an agent
M13-M14: You add planning and multi-agent — advanced patterns
M15B: You build a complete Level 3 agent from scratch
```

"Everything before M05 is Level 1. M05 adds tools. M12 adds the loop. That's when you cross the line from program to agent."

## Common Gray Areas

**"My code calls Claude, then based on the response calls Claude again. Agent?"**
→ NO. YOUR code decided to call again based on YOUR if/else logic. That's Level 2.

**"My code calls Claude with tools, Claude uses one tool, I return the result. Agent?"**
→ BORDERLINE. If it's always one tool call then stop → Level 1 with a tool. If Claude COULD call multiple tools and YOU loop until stop_reason is end_turn → Level 3.

**"I use LangChain's AgentExecutor. Is it an agent?"**
→ YES — if it has tools and a loop and Claude decides. The framework doesn't matter. The pattern matters.

**"My code calls Claude to decide which function to call, then MY code calls that function. Agent?"**
→ This is Level 2 with Claude as a router. Claude makes ONE decision (which function) but doesn't loop or adapt. Closer to Level 2.5 — a "router pattern" (M13).
