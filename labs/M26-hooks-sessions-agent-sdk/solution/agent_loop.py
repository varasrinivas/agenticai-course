"""
M26 Lab — Step 1: Agent SDK Agentic Loop

Demonstrates the agentic loop pattern used by the Agent SDK.
We simulate the SDK's query() function using the Messages API
to show exactly what happens under the hood.

Usage:
    python agent_loop.py
"""

import json
import os
from datetime import datetime


# --- Mock Anthropic client (no API key needed) ---

class MockToolResult:
    """Simulates tool execution results."""

    TOOL_HANDLERS = {
        "lookup_filing": lambda params: {
            "filing_number": params.get("filing_number", "UCC-2024-NY-0012847"),
            "status": "Active",
            "debtor": "Greenfield Logistics LLC",
            "secured_party": "Atlantic Capital Partners",
            "filing_date": "2024-03-15",
            "expiration_date": "2029-03-15",
            "collateral": "All accounts receivable, inventory, equipment"
        },
        "check_risk_profile": lambda params: {
            "entity": params.get("entity_name", "Greenfield Logistics LLC"),
            "risk_score": 0.35,
            "risk_level": "LOW",
            "factors": ["No prior defaults", "Active 5+ years", "Single active lien"],
            "last_updated": "2024-12-01"
        },
        "issue_refund": lambda params: {
            "refund_id": "REF-2024-0042",
            "amount": params.get("amount", 150.00),
            "status": "processed" if params.get("amount", 150) <= 500 else "blocked",
            "reason": "Within limit" if params.get("amount", 150) <= 500 else "Exceeds $500 limit — requires human approval"
        },
        "escalate_to_human": lambda params: {
            "ticket_id": "ESC-2024-0891",
            "priority": params.get("priority", "medium"),
            "reason": params.get("reason", "Policy gap detected"),
            "assigned_to": "support-team-lead",
            "eta_minutes": 15
        }
    }

    @classmethod
    def execute(cls, tool_name, tool_input):
        handler = cls.TOOL_HANDLERS.get(tool_name)
        if handler:
            return json.dumps(handler(tool_input))
        return json.dumps({"error": f"Unknown tool: {tool_name}", "isError": True})


# --- Tool definitions ---

TOOLS = [
    {
        "name": "lookup_filing",
        "description": "Look up a UCC filing by its filing number. Returns filing details including status, parties, and collateral.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filing_number": {
                    "type": "string",
                    "description": "Filing number in format UCC-YYYY-ST-NNNNNNN"
                }
            },
            "required": ["filing_number"]
        }
    },
    {
        "name": "check_risk_profile",
        "description": "Check the risk profile for a debtor or secured party entity.",
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_name": {
                    "type": "string",
                    "description": "Name of the entity to check"
                }
            },
            "required": ["entity_name"]
        }
    },
    {
        "name": "issue_refund",
        "description": "Issue a refund for a filing service fee. Amounts over $500 require human approval.",
        "input_schema": {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "Refund amount in dollars"
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for the refund"
                }
            },
            "required": ["amount", "reason"]
        }
    },
    {
        "name": "escalate_to_human",
        "description": "Escalate the current case to a human agent. Use for policy gaps or capability limits — NOT for angry customers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "critical"],
                    "description": "Escalation priority level"
                },
                "reason": {
                    "type": "string",
                    "description": "Why this case needs human review"
                },
                "context": {
                    "type": "string",
                    "description": "Summary of what has been attempted so far"
                }
            },
            "required": ["priority", "reason"]
        }
    }
]


# --- Simulated Agent SDK ---

class AgentResponse:
    """Mirrors the Agent SDK response structure."""
    def __init__(self, stop_reason, content, tool_calls=None):
        self.stop_reason = stop_reason
        self.content = content
        self.tool_calls = tool_calls or []


class SimulatedAgentSDK:
    """
    Simulates the Agent SDK's query() function.

    In the real Agent SDK:
        result = await query(prompt="...", tools=TOOLS, max_turns=10)

    Under the hood, the SDK runs this exact while loop.
    We make it explicit so you can see every step.
    """

    def __init__(self, tools, max_turns=10):
        self.tools = tools
        self.max_turns = max_turns
        self.turn_count = 0
        self.messages = []
        self.audit_log = []

    def query(self, prompt, system=None):
        """
        Simulate the Agent SDK's query() method.

        This is the AGENTIC LOOP:
        1. Send message to Claude
        2. Check stop_reason
        3. If stop_reason == 'tool_use' -> execute tools, continue loop
        4. If stop_reason == 'end_turn' -> task complete, return
        5. If stop_reason == 'max_tokens' -> handle gracefully
        6. Safety: stop if turn_count >= max_turns
        """
        self.messages = [{"role": "user", "content": prompt}]
        self.turn_count = 0

        print(f"\n{'='*60}")
        print(f"Agent SDK query() started")
        print(f"Prompt: {prompt[:80]}...")
        print(f"Max turns: {self.max_turns}")
        print(f"{'='*60}\n")

        while self.turn_count < self.max_turns:
            self.turn_count += 1

            # --- Simulate Claude's response ---
            response = self._simulate_claude_response()

            print(f"--- Turn {self.turn_count} ---")
            print(f"  stop_reason: {response.stop_reason}")

            # === THE CRITICAL CHECK ===
            # This is what the Agent SDK does automatically.
            # CORRECT: Check stop_reason to decide whether to continue.
            # WRONG: Parse the text output to guess if Claude is "done".

            if response.stop_reason == "end_turn":
                # Claude considers the task complete
                print(f"  -> Task complete. Final response delivered.")
                print(f"  Content: {response.content[:100]}...")
                self._log("end_turn", "Task completed naturally")
                return response

            elif response.stop_reason == "tool_use":
                # Claude wants to use a tool — execute it and continue
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_input = tool_call["input"]

                    print(f"  -> Tool call: {tool_name}({json.dumps(tool_input)[:60]}...)")

                    # Execute the tool
                    result = MockToolResult.execute(tool_name, tool_input)
                    print(f"  <- Result: {result[:80]}...")

                    self._log("tool_use", f"{tool_name}: {result[:50]}")

                    # Append tool result to conversation
                    self.messages.append({
                        "role": "assistant",
                        "content": [{"type": "tool_use", "id": f"call_{self.turn_count}", "name": tool_name, "input": tool_input}]
                    })
                    self.messages.append({
                        "role": "user",
                        "content": [{"type": "tool_result", "tool_use_id": f"call_{self.turn_count}", "content": result}]
                    })

            elif response.stop_reason == "max_tokens":
                # Ran out of tokens — handle gracefully
                print(f"  -> Max tokens reached. Attempting graceful recovery.")
                self._log("max_tokens", "Token limit hit")
                # In production: truncate context, retry with summary
                return response

        # Safety net: max_turns exceeded
        print(f"\n[!] Max turns ({self.max_turns}) reached — stopping loop.")
        print(f"  This is a SAFETY NET, not the primary stop mechanism.")
        self._log("max_turns_exceeded", f"Hit {self.max_turns} turn limit")
        return AgentResponse("max_turns", "Reached maximum turn limit.", [])

    def _simulate_claude_response(self):
        """
        Simulates Claude's response based on conversation state.
        In production, this would be an actual API call.
        """
        # Simulate a multi-turn agent flow:
        # Turn 1: Look up filing
        # Turn 2: Check risk profile
        # Turn 3: Deliver final answer

        if self.turn_count == 1:
            return AgentResponse("tool_use", "", [
                {"name": "lookup_filing", "input": {"filing_number": "UCC-2024-NY-0012847"}}
            ])
        elif self.turn_count == 2:
            return AgentResponse("tool_use", "", [
                {"name": "check_risk_profile", "input": {"entity_name": "Greenfield Logistics LLC"}}
            ])
        else:
            return AgentResponse(
                "end_turn",
                "Based on my research:\n\n"
                "**Filing UCC-2024-NY-0012847** is Active.\n"
                "- Debtor: Greenfield Logistics LLC\n"
                "- Secured Party: Atlantic Capital Partners\n"
                "- Risk Level: LOW (score: 0.35)\n"
                "- Expires: 2029-03-15\n\n"
                "No issues found. The filing is current and the debtor has a clean risk profile.",
                []
            )

    def _log(self, event_type, detail):
        self.audit_log.append({
            "turn": self.turn_count,
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            "detail": detail
        })

    def get_audit_log(self):
        return self.audit_log


# --- Main: Run the agent loop demo ---

def main():
    print("=" * 60)
    print("M26 Lab — Agent SDK Agentic Loop Demo")
    print("=" * 60)

    # Create the simulated SDK
    agent = SimulatedAgentSDK(tools=TOOLS, max_turns=10)

    # Run a query (this is what query() does in the real Agent SDK)
    result = agent.query(
        prompt="Look up filing UCC-2024-NY-0012847 and check if the debtor has any risk flags.",
        system="You are a UCC filing support agent. Use tools to look up filings and check risk profiles before answering."
    )

    # Print audit log
    print(f"\n{'='*60}")
    print("Audit Log:")
    print(f"{'='*60}")
    for entry in agent.get_audit_log():
        print(f"  Turn {entry['turn']}: [{entry['event']}] {entry['detail']}")

    # Demonstrate the anti-pattern
    print(f"\n{'='*60}")
    print("[!] ANTI-PATTERN WARNING")
    print(f"{'='*60}")
    print("""
    X WRONG — Parsing text to determine if done:
        if "I'm done" in response.text or "Here's your answer" in response.text:
            break

    CORRECT — Checking stop_reason:
        if response.stop_reason == "end_turn":
            break
        elif response.stop_reason == "tool_use":
            execute_tools(response.tool_calls)

    Why? The model's text is non-deterministic. It might say "done"
    mid-conversation or forget to say it when actually finished.
    stop_reason is the ONLY reliable termination signal.
    """)

    print("[OK] Lab Step 1 complete — agent loop with stop_reason handling\n")


if __name__ == "__main__":
    main()
