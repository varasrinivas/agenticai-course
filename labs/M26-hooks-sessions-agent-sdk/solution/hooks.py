"""
M26 Lab — Step 2: Pre/Post Tool Use Hooks

Hooks provide PROGRAMMATIC enforcement — they are guaranteed to run,
unlike prompt instructions which are probabilistic.

Analogy: Prompts are like asking a teenager to clean their room.
Hooks are like installing a lock on the liquor cabinet.

Usage:
    python hooks.py
"""

import json
import sys
from datetime import datetime


class HookEngine:
    """
    Simulates Claude Code's hook execution engine.

    In production, hooks are configured in .claude/settings.json:
    {
        "hooks": {
            "PreToolUse": [{"matcher": "issue_refund", "command": "python hooks/refund_check.py"}],
            "PostToolUse": [{"matcher": "*", "command": "python hooks/audit_log.py"}]
        }
    }

    Here we simulate the same logic in Python for learning purposes.
    """

    def __init__(self):
        self.pre_hooks = []
        self.post_hooks = []
        self.audit_trail = []
        self.blocked_count = 0

    def register_pre_hook(self, matcher, handler, description=""):
        """Register a PreToolUse hook."""
        self.pre_hooks.append({
            "matcher": matcher,
            "handler": handler,
            "description": description
        })

    def register_post_hook(self, matcher, handler, description=""):
        """Register a PostToolUse hook."""
        self.post_hooks.append({
            "matcher": matcher,
            "handler": handler,
            "description": description
        })

    def run_pre_hooks(self, tool_name, tool_input):
        """
        Run all matching PreToolUse hooks.
        Returns: (allowed: bool, reason: str)

        Hook return codes (matches Claude Code behavior):
        - Exit 0: Allow the tool call
        - Exit 2: BLOCK the tool call (with reason)
        """
        for hook in self.pre_hooks:
            if hook["matcher"] == "*" or hook["matcher"] == tool_name:
                result = hook["handler"](tool_name, tool_input)
                if not result["allowed"]:
                    self.blocked_count += 1
                    self.audit_trail.append({
                        "timestamp": datetime.now().isoformat(),
                        "phase": "PreToolUse",
                        "tool": tool_name,
                        "action": "BLOCKED",
                        "reason": result["reason"],
                        "hook": hook["description"]
                    })
                    return False, result["reason"]
        return True, "All pre-hooks passed"

    def run_post_hooks(self, tool_name, tool_input, tool_output):
        """Run all matching PostToolUse hooks after tool execution."""
        for hook in self.post_hooks:
            if hook["matcher"] == "*" or hook["matcher"] == tool_name:
                hook["handler"](tool_name, tool_input, tool_output)
                self.audit_trail.append({
                    "timestamp": datetime.now().isoformat(),
                    "phase": "PostToolUse",
                    "tool": tool_name,
                    "action": "LOGGED",
                    "hook": hook["description"]
                })

    def execute_with_hooks(self, tool_name, tool_input, tool_executor):
        """
        Full hook lifecycle:
        1. Run PreToolUse hooks -> block or allow
        2. If allowed, execute the tool
        3. Run PostToolUse hooks (logging, validation)
        4. Return result
        """
        print(f"\n  [Hook] Tool call: {tool_name}")
        print(f"     Input: {json.dumps(tool_input)[:80]}")

        # Phase 1: Pre-hooks
        allowed, reason = self.run_pre_hooks(tool_name, tool_input)
        if not allowed:
            print(f"     BLOCKED by PreToolUse hook: {reason}")
            return {"blocked": True, "reason": reason}

        print(f"     [OK] PreToolUse hooks passed")

        # Phase 2: Execute tool
        result = tool_executor(tool_name, tool_input)
        print(f"     <- Result: {json.dumps(result)[:80]}")

        # Phase 3: Post-hooks
        self.run_post_hooks(tool_name, tool_input, result)
        print(f"     [OK] PostToolUse hooks completed")

        return result


# --- Hook implementations ---

def refund_limit_hook(tool_name, tool_input):
    """
    PreToolUse hook: Block refunds over $500.

    This is the classic example of hooks vs prompts:
    - Prompt: "Never issue refunds over $500" -> works ~95% of the time
    - Hook: Programmatic check -> works 100% of the time

    For compliance-critical rules, ALWAYS use hooks.
    """
    if tool_name != "issue_refund":
        return {"allowed": True}

    amount = tool_input.get("amount", 0)
    if amount > 500:
        return {
            "allowed": False,
            "reason": f"Refund amount ${amount:.2f} exceeds $500 limit. "
                      f"Requires human approval. Escalate to support-team-lead."
        }
    return {"allowed": True}


def production_write_guard(tool_name, tool_input):
    """
    PreToolUse hook: Prevent writes to production data directory.
    """
    if tool_name != "Write":
        return {"allowed": True}

    file_path = tool_input.get("file_path", "")
    if "data/production" in file_path:
        return {
            "allowed": False,
            "reason": f"Cannot write to production data path: {file_path}"
        }
    return {"allowed": True}


def audit_log_hook(tool_name, tool_input, tool_output):
    """
    PostToolUse hook: Log every tool execution for audit compliance.

    In a real system, this would write to a persistent log file or
    send to a logging service. Here we print to demonstrate the pattern.
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "tool": tool_name,
        "input_summary": json.dumps(tool_input)[:100],
        "output_summary": json.dumps(tool_output)[:100],
        "status": "blocked" if isinstance(tool_output, dict) and tool_output.get("blocked") else "success"
    }
    print(f"     [Audit] {tool_name} -> {log_entry['status']}")


# --- Mock tool executor ---

def mock_tool_executor(tool_name, tool_input):
    """Executes tools with mock responses."""
    handlers = {
        "issue_refund": lambda inp: {
            "refund_id": "REF-2024-0042",
            "amount": inp.get("amount", 0),
            "status": "processed"
        },
        "lookup_filing": lambda inp: {
            "filing_number": inp.get("filing_number"),
            "status": "Active",
            "debtor": "Greenfield Logistics LLC"
        },
        "escalate_to_human": lambda inp: {
            "ticket_id": "ESC-2024-0891",
            "priority": inp.get("priority", "medium"),
            "status": "created"
        }
    }
    handler = handlers.get(tool_name, lambda inp: {"error": f"Unknown tool: {tool_name}"})
    return handler(tool_input)


# --- Main demo ---

def main():
    print("=" * 60)
    print("M26 Lab — Hooks: Programmatic Enforcement")
    print("=" * 60)

    # Set up the hook engine
    engine = HookEngine()

    # Register hooks
    engine.register_pre_hook(
        matcher="issue_refund",
        handler=refund_limit_hook,
        description="Block refunds > $500"
    )
    engine.register_pre_hook(
        matcher="Write",
        handler=production_write_guard,
        description="Block production data writes"
    )
    engine.register_post_hook(
        matcher="*",
        handler=audit_log_hook,
        description="Audit trail logger"
    )

    # Test scenarios
    print("\n--- Scenario 1: Small refund (should PASS) ---")
    engine.execute_with_hooks(
        "issue_refund",
        {"amount": 150.00, "reason": "Duplicate filing fee"},
        mock_tool_executor
    )

    print("\n--- Scenario 2: Large refund (should BLOCK) ---")
    engine.execute_with_hooks(
        "issue_refund",
        {"amount": 750.00, "reason": "Customer dispute"},
        mock_tool_executor
    )

    print("\n--- Scenario 3: Filing lookup (no refund hook, should PASS) ---")
    engine.execute_with_hooks(
        "lookup_filing",
        {"filing_number": "UCC-2024-NY-0012847"},
        mock_tool_executor
    )

    print("\n--- Scenario 4: Write to production (should BLOCK) ---")
    engine.execute_with_hooks(
        "Write",
        {"file_path": "data/production/filings.db"},
        mock_tool_executor
    )

    # Print summary
    print(f"\n{'='*60}")
    print("Hook Execution Summary")
    print(f"{'='*60}")
    print(f"  Total hook events: {len(engine.audit_trail)}")
    print(f"  Blocked calls: {engine.blocked_count}")
    print(f"  Audit trail entries:")
    for entry in engine.audit_trail:
        print(f"    [{entry['phase']}] {entry['tool']} -> {entry['action']}")

    print(f"\n{'='*60}")
    print("Key Takeaway: Hooks vs Prompts")
    print(f"{'='*60}")
    print("""
    Use PROMPTS for:          Use HOOKS for:
    ----------------------    ----------------------
    Style & tone              Spending limits
    Response format           Data access control
    Personality               Compliance rules
    Non-critical guidance     Audit logging
                              PII redaction

    Prompts = suggestions (probabilistic, ~95%)
    Hooks  = rules (deterministic, 100%)
    """)

    print("[OK] Lab Step 2 complete — Pre/Post tool use hooks\n")


if __name__ == "__main__":
    main()
