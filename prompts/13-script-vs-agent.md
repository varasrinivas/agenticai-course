# Script vs Agent Comparison

This document defines a side-by-side comparison using a REAL problem that students encounter in the UCC domain. This comparison should be added to M00 (overview) as a high-level preview and to M12 (ReAct) as the detailed implementation comparison.

## The Problem: "Find the total lien exposure for Acme Corporation"

This single question requires:
1. Search for filings under "Acme Corporation"
2. Search for name variations: "ACME CORP" and "ACME CORPORATION INC"
3. Search across multiple states (NY and CA and TX)
4. Filter out terminated and lapsed filings
5. Sum the active collateral descriptions
6. Generate a human-readable summary

## Approach A: Traditional Python Script

```python
# script_approach.py — The traditional way
import json

def find_lien_exposure(company_name):
    # Step 1: Hardcoded name variations — YOU must think of every variant
    name_variants = [
        company_name,
        company_name.upper(),
        company_name.replace("Corporation", "Corp"),
        company_name.replace("Corporation", "Corp."),
        company_name.replace("Corporation", "Corporation Inc"),
    ]
    
    # Step 2: Hardcoded state list — YOU must know which states to search
    states = ["NY", "CA", "TX", "FL", "IL", "DE"]
    
    # Step 3: Hardcoded search logic — rigid loop
    all_filings = []
    for state in states:
        for name in name_variants:
            results = search_database(name, state)  # YOU write the query
            all_filings.extend(results)
    
    # Step 4: Hardcoded filter — YOU define what "active" means
    active_filings = [
        f for f in all_filings
        if f["status"] == "ACTIVE"
        and f["lapse_date"] > today()
    ]
    
    # Step 5: Deduplication — YOU handle edge cases
    seen_ids = set()
    unique_filings = []
    for f in active_filings:
        if f["filing_number"] not in seen_ids:
            seen_ids.add(f["filing_number"])
            unique_filings.append(f)
    
    # Step 6: Hardcoded report format
    total_count = len(unique_filings)
    states_found = set(f["state"] for f in unique_filings)
    
    return {
        "company": company_name,
        "total_active_filings": total_count,
        "states": list(states_found),
        "filings": unique_filings
    }

# PROBLEMS WITH THIS APPROACH:
# 1. Name variations are hardcoded — misses "ACME CORP DBA ROADRUNNER SUPPLIES"
# 2. State list is hardcoded — misses filings in OH, PA, GA
# 3. No reasoning about WHAT to search next — blind loop
# 4. Can not handle unexpected data (new filing types, unusual formats)
# 5. Report format is rigid — can not adapt to follow-up questions
# 6. Every new edge case = code change + redeploy
# 7. Can not explain WHY it searched what it searched
```

## Approach B: Agent with Claude

```python
# agent_approach.py — The agent way
import anthropic

client = anthropic.Anthropic()
tools = [
    {
        "name": "search_filings",
        "description": "Search UCC filings by debtor name in a specific state",
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {"type": "string"},
                "state": {"type": "string"}
            },
            "required": ["debtor_name"]
        }
    },
    {
        "name": "get_filing_details",
        "description": "Get full details for a specific filing",
        "input_schema": {
            "type": "object",
            "properties": {
                "filing_number": {"type": "string"}
            },
            "required": ["filing_number"]
        }
    }
]

def find_lien_exposure(question):
    messages = [{"role": "user", "content": question}]
    
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system="You are a UCC filing research agent. Search thoroughly using name variations and multiple states.",
            tools=tools,
            messages=messages
        )
        
        if response.stop_reason == "end_turn":
            return response.content[0].text
        
        # Claude decides what to search — not hardcoded
        for block in response.content:
            if block.type == "tool_use":
                result = execute_tool(block.name, block.input)
                messages.append({"role": "assistant", "content": response.content})
                messages.append({
                    "role": "user",
                    "content": [{"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(result)}]
                })

# WHAT THE AGENT DOES (you did NOT code this logic):
# Turn 1: Claude thinks "I should search for the exact name first"
#          → calls search_filings("Acme Corporation", "NY") → finds 4 filings
# Turn 2: Claude thinks "I should check common abbreviations"
#          → calls search_filings("ACME CORP") → finds 3 more in CA and TX
# Turn 3: Claude thinks "Let me check for DBAs too"
#          → calls search_filings("ACME") → finds "ACME CORP DBA ROADRUNNER SUPPLIES" in FL
# Turn 4: Claude thinks "I have 8 filings across 4 states — let me check which are active"
#          → filters by status and lapse date
# Turn 5: Claude thinks "I have enough data to answer"
#          → generates a natural language summary with totals and state breakdown
#
# ADVANTAGES OVER THE SCRIPT:
# 1. Name variations are DISCOVERED by reasoning — not hardcoded
# 2. States are searched based on results — not a fixed list
# 3. Claude DECIDES what to search next based on what it found
# 4. Handles unexpected data by reasoning about it
# 5. Response adapts to the question — follow-ups work naturally
# 6. New edge cases handled by reasoning — no code change needed
# 7. Full thought trace explains every decision
```

## Side-by-Side Comparison Table

| Aspect | Script | Agent |
|---|---|---|
| Name variations | Hardcoded list YOU maintain | Discovered by reasoning at runtime |
| States to search | Fixed list | Dynamic based on findings |
| Decision logic | if/else chains YOU write | Claude reasons about what to do next |
| New edge cases | Code change + redeploy | Handled by reasoning — no code change |
| Follow-up questions | Build a new function | Natural conversation continuation |
| Explainability | Add logging manually | Thought trace built in |
| Error handling | try/except for every case | Claude adapts and retries |
| Report format | Hardcoded template | Adapts to question and audience |
| Development time | Days (handle every case) | Hours (define tools + loop) |
| Maintenance | Every edge case = code change | Update tools only when data sources change |

## When Scripts ARE Better Than Agents

Agents are NOT always the answer. Scripts win when:
- The task is 100% deterministic (no reasoning needed)
- Speed matters more than flexibility (scripts are 100x faster)
- Cost matters (agent = API calls = money per request)
- The logic never changes (agents add unnecessary complexity)
- You need guaranteed reproducibility (same input = same output every time)

Examples where a script beats an agent:
- File format conversion (CSV to JSON)
- Data validation against a fixed schema
- Batch record insertion
- Cron jobs with fixed logic
- Simple CRUD operations

## The Key Insight for Students

"An agent is a script that replaced the hardcoded decision logic with an LLM. Instead of YOU writing every if/else and every loop condition, Claude REASONS about what to do next. Your code provides the TOOLS (what the agent CAN do). Claude provides the LOGIC (what the agent SHOULD do)."

"The tool use loop you wrote (15 lines) replaces hundreds of lines of decision logic. But you still write the tools — the agent does not magically connect to databases or APIs. YOU provide the hands. Claude provides the brain."

## Where to Add This Comparison

### M00 (Course Overview) — High-Level Preview
Add a condensed version (the comparison table + the key insight paragraph) as a new section between "What Is an Agent?" and "See an Agent in Action." Title: "Script vs Agent: Why This Course Exists"

The student sees the comparison BEFORE they know how to build either one. It motivates the entire course.

### M12 (ReAct) — Full Implementation
Add the complete comparison (both code listings + table + when scripts win) as the FIRST section of M12 before the ReAct explanation. Title: "From Script to Agent: The Problem That Agents Solve"

The student sees both implementations side by side and understands exactly what the ReAct loop replaces.

### Animated Diagram for Both Modules
A side-by-side animation:
- LEFT: Script approach — rigid arrows flowing through hardcoded boxes (fixed list → fixed loop → fixed filter → fixed report)
- RIGHT: Agent approach — think bubbles deciding dynamically (think → search → observe → think → search different thing → observe → synthesize)

The script side is GRAY (rigid). The agent side is COLORED (dynamic). The agent side shows new paths appearing that the script side cannot follow.
