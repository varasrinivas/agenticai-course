"""
M26 Lab — Step 5: Full Customer Support Agent

Composes all previous steps into a production-grade UCC filing
customer support agent with hooks, sessions, and subagent delegation.

YOUR TASK: Fill in the TODO sections to compose the full agent.

Usage:
    python support_agent.py
"""

import json
import copy
from datetime import datetime


# =========================================================================
# Components from Steps 1-4 (simplified for composition)
# =========================================================================

# --- Mock tool execution (from Step 1) ---

MOCK_TOOLS = {
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
        "factors": ["No prior defaults", "Active 5+ years", "Single active lien"]
    },
    "issue_refund": lambda params: {
        "refund_id": "REF-2024-0042",
        "amount": params.get("amount", 150.00),
        "status": "processed" if params.get("amount", 150) <= 500 else "blocked"
    },
    "escalate_to_human": lambda params: {
        "ticket_id": "ESC-2024-0891",
        "priority": params.get("priority", "medium"),
        "reason": params.get("reason", "Policy gap"),
        "assigned_to": "support-team-lead",
        "eta_minutes": 15
    },
    "resolve_entity": lambda params: {
        "canonical_name": params.get("entity_name", ""),
        "related_entities": ["Greenfield Logistics West LLC"],
        "states": ["NY", "CA"],
        "confidence": 0.95
    }
}


# --- Hook Engine (from Step 2) ---

class HookEngine:
    def __init__(self):
        self.pre_hooks = []
        self.post_hooks = []
        self.audit_trail = []
        self.blocked_count = 0

    def register_pre_hook(self, matcher, handler, description=""):
        self.pre_hooks.append({"matcher": matcher, "handler": handler, "description": description})

    def register_post_hook(self, matcher, handler, description=""):
        self.post_hooks.append({"matcher": matcher, "handler": handler, "description": description})

    def execute_with_hooks(self, tool_name, tool_input, tool_executor):
        # Pre-hooks
        for hook in self.pre_hooks:
            if hook["matcher"] == "*" or hook["matcher"] == tool_name:
                result = hook["handler"](tool_name, tool_input)
                if not result.get("allowed", True):
                    self.blocked_count += 1
                    self.audit_trail.append({
                        "timestamp": datetime.now().isoformat(),
                        "phase": "PreToolUse",
                        "tool": tool_name,
                        "action": "BLOCKED",
                        "reason": result["reason"]
                    })
                    return {"blocked": True, "reason": result["reason"]}

        # Execute
        tool_result = tool_executor(tool_name, tool_input)

        # Post-hooks
        for hook in self.post_hooks:
            if hook["matcher"] == "*" or hook["matcher"] == tool_name:
                hook["handler"](tool_name, tool_input, tool_result)
                self.audit_trail.append({
                    "timestamp": datetime.now().isoformat(),
                    "phase": "PostToolUse",
                    "tool": tool_name,
                    "action": "LOGGED"
                })

        return tool_result


# --- Session Manager (from Step 3) ---

class SessionManager:
    def __init__(self):
        self.sessions = {}

    def create_session(self, name, system_prompt=""):
        self.sessions[name] = {
            "name": name,
            "system_prompt": system_prompt,
            "messages": [],
            "token_count": 0,
            "created_at": datetime.now().isoformat()
        }
        return self.sessions[name]

    def add_message(self, session_name, role, content):
        session = self.sessions.get(session_name)
        if session:
            session["messages"].append({"role": role, "content": content, "timestamp": datetime.now().isoformat()})
            session["token_count"] += len(content) // 4

    def fork_session(self, source_name, fork_name):
        source = self.sessions.get(source_name)
        if source:
            self.sessions[fork_name] = copy.deepcopy(source)
            self.sessions[fork_name]["name"] = fork_name
            self.sessions[fork_name]["parent"] = source_name
            return self.sessions[fork_name]
        return None

    def get_session(self, name):
        return self.sessions.get(name)


# --- Subagent Coordinator (from Step 4) ---

class SubAgentCoordinator:
    def __init__(self):
        self.results = {}

    def delegate_entity_research(self, entity_name):
        """Delegate cross-state entity research to subagents."""
        print(f"      [Coordinator] Decomposing entity research for: {entity_name}")

        # Subagent 1: Entity resolution
        entity_result = MOCK_TOOLS["resolve_entity"]({"entity_name": entity_name})
        print(f"      [EntityAgent] Resolved: {entity_result['canonical_name']} -> {entity_result['related_entities']}")

        # Subagent 2: Filing search (for each entity)
        all_filings = []
        all_entities = [entity_name] + entity_result.get("related_entities", [])
        for ent in all_entities:
            filing = MOCK_TOOLS["lookup_filing"]({"filing_number": f"search:{ent}"})
            all_filings.append({"entity": ent, "filing": filing})
            print(f"      [FilingAgent] Found filing for {ent}: {filing['status']}")

        # Subagent 3: Risk scoring (aggregate)
        risk_profiles = []
        for ent in all_entities:
            risk = MOCK_TOOLS["check_risk_profile"]({"entity_name": ent})
            risk_profiles.append({"entity": ent, "risk": risk})
            print(f"      [RiskAgent] {ent}: {risk['risk_level']} ({risk['risk_score']})")

        # Aggregate
        avg_risk = sum(r["risk"]["risk_score"] for r in risk_profiles) / len(risk_profiles)
        return {
            "entities": all_entities,
            "states": entity_result.get("states", []),
            "filings": all_filings,
            "risk_profiles": risk_profiles,
            "aggregate_risk": round(avg_risk, 3),
            "aggregate_level": "LOW" if avg_risk < 0.4 else "MEDIUM" if avg_risk < 0.7 else "HIGH"
        }


# =========================================================================
# Support Agent — Composes everything
# =========================================================================

class SupportAgent:
    """
    Full customer support agent for UCC filing services.

    Composes:
    - Agent loop with stop_reason handling (Step 1)
    - Hook-based enforcement (Step 2)
    - Session management (Step 3)
    - Subagent delegation (Step 4)
    """

    def __init__(self):
        # Initialize components
        self.hooks = HookEngine()
        self.sessions = SessionManager()
        self.coordinator = SubAgentCoordinator()
        self.request_count = 0

        # TODO: Register hooks
        #
        # 1. Register a pre-hook on "issue_refund" matcher that calls self._refund_limit_hook
        #    Description: "Block refunds > $500"
        # 2. Register a post-hook on "*" matcher that calls self._audit_hook
        #    Description: "Audit trail"

        # <-- Your hook registration goes here

        print("  [SupportAgent] Initialized with hooks, sessions, and subagent coordinator")

    def _refund_limit_hook(self, tool_name, tool_input):
        """PreToolUse hook: Block refunds over $500."""
        if tool_name != "issue_refund":
            return {"allowed": True}
        amount = tool_input.get("amount", 0)
        if amount > 500:
            return {
                "allowed": False,
                "reason": f"Refund ${amount:.2f} exceeds $500 limit. Requires human approval."
            }
        return {"allowed": True}

    def _audit_hook(self, tool_name, tool_input, tool_output):
        """Post-hook: log every tool execution."""
        pass  # Logging handled by HookEngine's audit_trail

    def _execute_tool(self, tool_name, tool_input):
        handler = MOCK_TOOLS.get(tool_name)
        if handler:
            return handler(tool_input)
        return {"error": f"Unknown tool: {tool_name}"}

    def handle_request(self, request_text, customer_id="CUST-001"):
        """
        Process a customer support request through the full pipeline.

        1. Create/resume session
        2. Classify the request
        3. Execute via agent loop with hooks
        4. Delegate to subagents if needed
        5. Return response
        """
        self.request_count += 1
        session_name = f"session-{customer_id}-{self.request_count}"

        print(f"\n  --- Request #{self.request_count} ---")
        print(f"  Customer: {customer_id}")
        print(f"  Request: {request_text}")
        print(f"  Session: {session_name}")

        # Create session
        session = self.sessions.create_session(
            session_name,
            "You are a UCC filing support agent."
        )
        self.sessions.add_message(session_name, "user", request_text)

        # Classify request type (simplified pattern matching)
        request_type = self._classify_request(request_text)
        print(f"  Classified as: {request_type}")

        # TODO: Route based on request type
        #
        # If request_type == "filing_lookup":
        #     return self._handle_filing_lookup(session_name, request_text)
        # elif request_type == "refund":
        #     return self._handle_refund(session_name, request_text)
        # elif request_type == "entity_research":
        #     return self._handle_entity_research(session_name, request_text)
        # else:
        #     return self._handle_general(session_name, request_text)

        pass  # <-- Replace this with your implementation

    def _classify_request(self, text):
        text_lower = text.lower()
        if "refund" in text_lower:
            return "refund"
        elif "look up" in text_lower or "filing" in text_lower and "research" not in text_lower:
            return "filing_lookup"
        elif "research" in text_lower or "cross-state" in text_lower or "entity" in text_lower:
            return "entity_research"
        return "general"

    def _handle_filing_lookup(self, session_name, request_text):
        """Simple filing lookup — single turn, no subagents needed."""
        print(f"\n  [AgentLoop] Starting filing lookup (max 3 turns)")

        # TODO: Implement filing lookup
        #
        # Turn 1: Call self.hooks.execute_with_hooks("lookup_filing", {"filing_number": "UCC-2024-NY-0012847"}, self._execute_tool)
        #   - Print: f"    Turn 1: lookup_filing -> {result['status']}"
        #
        # Turn 2: Call self.hooks.execute_with_hooks("check_risk_profile", {"entity_name": result.get("debtor", "Unknown")}, self._execute_tool)
        #   - Print: f"    Turn 2: check_risk_profile -> {risk.get('risk_level', 'N/A')}"
        #
        # Turn 3: Build a response string with filing details and risk info
        #   - Add the response to the session: self.sessions.add_message(session_name, "assistant", response)
        #   - Print: f"    Turn 3: end_turn -> response delivered"
        #   - Print the response
        #   - Return {"status": "completed", "response": response}

        pass  # <-- Replace this with your implementation

    def _handle_refund(self, session_name, request_text):
        """Refund request — hooks may block, escalation may follow."""
        # Extract amount (simplified)
        amount = 750.00 if "750" in request_text else 150.00
        print(f"\n  [AgentLoop] Processing refund of ${amount:.2f}")

        # TODO: Implement refund handling with hook enforcement
        #
        # 1. Call self.hooks.execute_with_hooks("issue_refund", {"amount": amount, "reason": "Customer request"}, self._execute_tool)
        #
        # 2. If result has "blocked" key:
        #    - Print that refund was blocked
        #    - Escalate: call self.hooks.execute_with_hooks("escalate_to_human", {...}, self._execute_tool)
        #      with priority "high" and reason about the amount exceeding limit
        #    - Build response explaining the block and escalation
        #    - Add to session, print, return {"status": "escalated", "response": response, "ticket_id": ...}
        #
        # 3. If not blocked:
        #    - Build response confirming the refund
        #    - Add to session, print, return {"status": "completed", "response": response}
        #
        # KEY INSIGHT: The escalation happens because of a POLICY GAP (amount > $500),
        # NOT because of customer sentiment.

        pass  # <-- Replace this with your implementation

    def _handle_entity_research(self, session_name, request_text):
        """Cross-state entity research — delegate to subagents."""
        entity_name = "Greenfield Logistics LLC"  # Simplified extraction
        print(f"\n  [AgentLoop] Delegating to subagent coordinator")
        print(f"    Entity: {entity_name}")

        # TODO: Implement entity research with subagent delegation
        #
        # 1. Fork the session: self.sessions.fork_session(session_name, f"{session_name}-research-fork")
        #    - Print the fork name
        # 2. Delegate: research = self.coordinator.delegate_entity_research(entity_name)
        # 3. Build response from aggregated results including:
        #    - Number of entities found
        #    - States covered
        #    - Total filings
        #    - Aggregate risk level and score
        #    - Individual risk profiles
        # 4. Add to session, print, return {"status": "completed", "response": response}

        pass  # <-- Replace this with your implementation

    def _handle_general(self, session_name, request_text):
        response = "I can help with filing lookups, refund requests, and entity research. How can I assist you?"
        self.sessions.add_message(session_name, "assistant", response)
        print(f"\n  Response: {response}")
        return {"status": "completed", "response": response}


# =========================================================================
# Main — Run test scenarios
# =========================================================================

def main():
    print("=" * 60)
    print("M26 Lab — Full Customer Support Agent")
    print("=" * 60)

    agent = SupportAgent()

    # --- Scenario 1: Simple filing lookup ---
    print(f"\n{'='*60}")
    print("SCENARIO 1: Simple Filing Lookup")
    print(f"{'='*60}")
    result1 = agent.handle_request(
        "Look up filing UCC-2024-NY-0012847 and check for risk flags.",
        customer_id="CUST-100"
    )
    if result1:
        print(f"\n  Status: {result1['status']}")
    else:
        print("\n  [!] No result — check your handle_request implementation")

    # --- Scenario 2: Refund over $500 (blocked + escalated) ---
    print(f"\n{'='*60}")
    print("SCENARIO 2: Refund Request Over $500")
    print(f"{'='*60}")
    result2 = agent.handle_request(
        "I need a refund of $750 for duplicate filing charges.",
        customer_id="CUST-200"
    )
    if result2:
        print(f"\n  Status: {result2['status']}")
        if result2.get("ticket_id"):
            print(f"  Escalation ticket: {result2['ticket_id']}")
    else:
        print("\n  [!] No result — check your handle_request implementation")

    # --- Scenario 3: Cross-state entity research (subagent delegation) ---
    print(f"\n{'='*60}")
    print("SCENARIO 3: Cross-State Entity Research")
    print(f"{'='*60}")
    result3 = agent.handle_request(
        "Research Greenfield Logistics LLC across all states. Find related entities and aggregate risk.",
        customer_id="CUST-300"
    )
    if result3:
        print(f"\n  Status: {result3['status']}")
    else:
        print("\n  [!] No result — check your handle_request implementation")

    # --- Summary ---
    print(f"\n{'='*60}")
    print("Agent Execution Summary")
    print(f"{'='*60}")
    print(f"  Total requests handled: {agent.request_count}")
    print(f"  Hook audit trail entries: {len(agent.hooks.audit_trail)}")
    print(f"  Hooks blocked: {agent.hooks.blocked_count}")
    print(f"  Sessions created: {len(agent.sessions.sessions)}")

    print(f"\n  Audit trail:")
    for entry in agent.hooks.audit_trail:
        print(f"    [{entry['phase']}] {entry['tool']} -> {entry['action']}")

    print(f"\n  Sessions:")
    for name, session in agent.sessions.sessions.items():
        parent = session.get("parent", "")
        parent_label = f" [forked from {parent}]" if parent else ""
        print(f"    {name}{parent_label}: {len(session['messages'])} messages")

    print(f"\n{'='*60}")
    print("Key Takeaways — Composition")
    print(f"{'='*60}")
    print("""
    1. Agent loop: stop_reason drives the control flow (not text parsing)
    2. Hooks: Refund blocked DETERMINISTICALLY by PreToolUse hook (not prompt)
    3. Sessions: Each request gets its own session; research gets a fork
    4. Subagents: Complex research delegated to specialized subagents
    5. Escalation: Triggered by POLICY GAPS ($750 > $500), not customer sentiment

    This is the Agent SDK pattern in practice:
    - The SDK runs the loop (query())
    - Hooks enforce rules (settings.json)
    - Sessions manage state (named, forked)
    - Subagents handle complexity (isolated context)
    """)

    print("[OK] Lab Step 5 complete — Full customer support agent\n")


if __name__ == "__main__":
    main()
