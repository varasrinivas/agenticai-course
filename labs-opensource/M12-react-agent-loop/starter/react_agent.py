"""
M12 Lab - Step 2: The ReAct Research Agent
===========================================
Reason → Act → Observe → Repeat, with visible thought traces.
Run: python react_agent.py
"""

import json

from openai import OpenAI
from mock_search import mock_search

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

# The system prompt IS the ReAct pattern — it demands visible reasoning (COMPLETE)
SYSTEM_PROMPT = """You are a research assistant that compiles accurate, well-sourced reports.

IMPORTANT: Before EVERY tool call, write:
  Thought: [your reasoning — what you know, what's missing, why THIS tool call]

After EVERY tool result, write:
  Thought: [what you learned and whether you need more information]

When you have enough information, produce a structured report with:
- Summary (2-3 sentences)
- Key Findings (bullet points)
- Sources Used (list the searches you ran)"""

TOOLS = [{
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Search the web for current information about AI, technology, or "
            "research topics. Use specific queries for better results."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query — be specific (e.g., 'claude agent sdk features 2025' not 'claude')",
                }
            },
            "required": ["query"],
        },
    },
}]


def execute_tool(name: str, inputs: dict) -> str:
    """(COMPLETE) Dispatch a tool call to its implementation."""
    if name == "web_search":
        return mock_search(inputs.get("query", ""))
    return json.dumps({"error": f"Unknown tool: {name}", "isError": True})


def run_agent(question: str, max_turns: int = 20, verbose: bool = True) -> str:
    """Run the ReAct loop until finish_reason == 'stop'.

    TODO:
    messages = [{"role": "user", "content": question}]; turn = 0
    While turn < max_turns:
      1. turn += 1
      2. response = client.chat.completions.create(model="mistral",
             messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
             tools=TOOLS)
         (try/except → return f"API error: {e}")
      3. msg = response.choices[0].message
      4. If verbose:
           print(f"\\n--- Turn {turn} ---")
           if msg.content: print(f"Thought: {msg.content[:300]}")  ← the ReAct part!
           for tc in (msg.tool_calls or []): print the tool name + args
      5. If response.choices[0].finish_reason == "stop":
           return msg.content or "Agent completed without final text."
      6. Append the assistant message — KEEP msg.content (the thought is part
         of history!): {"role": "assistant", "content": msg.content,
                        "tool_calls": msg.tool_calls}
      7. OBSERVE: for each tc, execute_tool(...), append
         {"role": "tool", "tool_call_id": tc.id, "content": result}
    After the loop: return f"[Safety cap reached after {max_turns} turns]"
    """
    pass  # Remove this line when you add your code


# ── Test harness (COMPLETE) ──
if __name__ == "__main__":
    question = (
        "What are the main Python frameworks for building AI agents in 2025, "
        "and how does the claude-agent-sdk compare to them?"
    )
    answer = run_agent(question, verbose=True)
    print("\n" + "=" * 60)
    print("FINAL REPORT:")
    print("=" * 60)
    print(answer)
