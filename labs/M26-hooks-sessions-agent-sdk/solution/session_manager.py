"""
M26 Lab — Step 3: Session Management with Fork

Sessions allow an agent to persist conversation state across interactions
and branch into parallel explorations without polluting the main context.

Usage:
    python session_manager.py
"""

import json
import copy
import time
from datetime import datetime, timedelta


class Session:
    """
    Represents a single agent session with message history,
    token tracking, and metadata.
    """

    def __init__(self, name, system_prompt="", parent_name=None):
        self.name = name
        self.system_prompt = system_prompt
        self.parent_name = parent_name
        self.messages = []
        self.created_at = datetime.now()
        self.last_active = datetime.now()
        self.token_count = 0
        self.max_tokens = 100000  # Simulated context window
        self.metadata = {}

    def to_dict(self):
        return {
            "name": self.name,
            "system_prompt": self.system_prompt[:50] + "...",
            "parent": self.parent_name,
            "messages": len(self.messages),
            "tokens": self.token_count,
            "created": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
        }


class SessionManager:
    """
    Manages named sessions with create, resume, fork, and compact operations.

    Key concepts:
    - Named sessions: persist and resume by name
    - fork_session: branch a session for parallel exploration
    - Stale context detection: warn when session data may be outdated
    - Context compaction: summarize old messages to reclaim token budget
    """

    def __init__(self):
        self.sessions = {}
        self.active_session = None

    def create_session(self, name, system_prompt=""):
        """
        Create a new named session.

        Sessions are like browser tabs — each has its own conversation
        history, system prompt, and context window budget.
        """
        if name in self.sessions:
            print(f"  [!] Session '{name}' already exists. Use resume_session() instead.")
            return self.sessions[name]

        session = Session(name=name, system_prompt=system_prompt)
        self.sessions[name] = session
        self.active_session = session

        print(f"  [+] Created session: '{name}'")
        print(f"      System prompt: {system_prompt[:60]}...")
        return session

    def resume_session(self, name):
        """Resume an existing session by name."""
        if name not in self.sessions:
            print(f"  [!] Session '{name}' not found.")
            return None

        session = self.sessions[name]
        session.last_active = datetime.now()
        self.active_session = session

        print(f"  [>] Resumed session: '{name}' ({len(session.messages)} messages)")
        return session

    def add_message(self, role, content, session_name=None):
        """
        Add a message to a session and track approximate token usage.

        Token estimation: ~4 chars per token (rough approximation).
        In production, use tiktoken or the API's usage field.
        """
        session = self._get_session(session_name)
        if not session:
            return

        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        session.messages.append(message)

        # Approximate token count (4 chars ~ 1 token)
        estimated_tokens = len(content) // 4
        session.token_count += estimated_tokens
        session.last_active = datetime.now()

        print(f"  [{role}] {content[:60]}...")
        print(f"      Tokens: ~{session.token_count}/{session.max_tokens}")

        # Warn if approaching context limit
        usage_pct = session.token_count / session.max_tokens
        if usage_pct > 0.8:
            print(f"      [!] Context window {usage_pct:.0%} full — consider compaction")

        return message

    def fork_session(self, source_name, fork_name):
        """
        Create a branch from an existing session (deep copy).

        Use cases:
        - "What-if" analysis: explore a hypothesis without polluting main context
        - Parallel subagent exploration: fork, let subagent explore, merge or discard
        - A/B testing: fork, try two different approaches, compare results

        IMPORTANT: This is a deep copy. Changes to the fork do NOT
        affect the original session, and vice versa.
        """
        if source_name not in self.sessions:
            print(f"  [!] Source session '{source_name}' not found.")
            return None

        if fork_name in self.sessions:
            print(f"  [!] Fork name '{fork_name}' already exists.")
            return None

        source = self.sessions[source_name]

        # Deep copy to ensure isolation
        forked = Session(
            name=fork_name,
            system_prompt=source.system_prompt,
            parent_name=source_name
        )
        forked.messages = copy.deepcopy(source.messages)
        forked.token_count = source.token_count
        forked.metadata = copy.deepcopy(source.metadata)

        self.sessions[fork_name] = forked

        print(f"  [Fork] '{source_name}' -> '{fork_name}'")
        print(f"      Copied {len(forked.messages)} messages, ~{forked.token_count} tokens")
        return forked

    def is_context_stale(self, session_name=None, max_age_minutes=30, max_token_pct=0.7):
        """
        Detect when a session's context may be outdated.

        A session is considered stale if:
        1. It has been inactive for longer than max_age_minutes
        2. Its token usage exceeds max_token_pct of the context window

        Stale context can lead to:
        - Hallucinations based on outdated information
        - Contradictions with recent tool results
        - Inefficient token usage on irrelevant history
        """
        session = self._get_session(session_name)
        if not session:
            return False

        reasons = []

        # Check age
        age = datetime.now() - session.last_active
        if age > timedelta(minutes=max_age_minutes):
            reasons.append(f"Inactive for {age.total_seconds() / 60:.0f} min (limit: {max_age_minutes} min)")

        # Check token usage
        usage_pct = session.token_count / session.max_tokens
        if usage_pct > max_token_pct:
            reasons.append(f"Token usage {usage_pct:.0%} (limit: {max_token_pct:.0%})")

        is_stale = len(reasons) > 0

        if is_stale:
            print(f"  [!] Session '{session.name}' is STALE:")
            for reason in reasons:
                print(f"      - {reason}")
        else:
            print(f"  [OK] Session '{session.name}' is fresh")

        return is_stale

    def compact_session(self, session_name=None, keep_recent=3):
        """
        Summarize old messages to reclaim context window space.

        Strategy:
        1. Keep the system prompt (always)
        2. Keep the most recent N messages (keep_recent)
        3. Replace older messages with a summary

        In production, you would call Claude to generate the summary.
        Here we simulate it for demonstration.
        """
        session = self._get_session(session_name)
        if not session:
            return

        if len(session.messages) <= keep_recent:
            print(f"  [OK] Session '{session.name}' has {len(session.messages)} messages — no compaction needed")
            return

        old_count = len(session.messages)
        old_tokens = session.token_count

        # Messages to summarize
        to_summarize = session.messages[:-keep_recent]
        recent = session.messages[-keep_recent:]

        # Generate summary (simulated — in production, call Claude)
        summary_parts = []
        for msg in to_summarize:
            summary_parts.append(f"[{msg['role']}] {msg['content'][:40]}...")

        summary = {
            "role": "system",
            "content": f"[Compacted summary of {len(to_summarize)} earlier messages]\n" + "\n".join(summary_parts),
            "timestamp": datetime.now().isoformat(),
            "is_summary": True
        }

        # Replace messages
        session.messages = [summary] + recent

        # Recalculate token count
        new_tokens = sum(len(m["content"]) // 4 for m in session.messages)
        session.token_count = new_tokens

        print(f"  [Compact] Session '{session.name}':")
        print(f"      Messages: {old_count} -> {len(session.messages)}")
        print(f"      Tokens: ~{old_tokens} -> ~{new_tokens} (saved ~{old_tokens - new_tokens})")

    def list_sessions(self):
        """List all sessions with their status."""
        print(f"\n  Active sessions: {len(self.sessions)}")
        for name, session in self.sessions.items():
            active_marker = " (ACTIVE)" if session == self.active_session else ""
            fork_marker = f" [forked from {session.parent_name}]" if session.parent_name else ""
            print(f"    - {name}{active_marker}{fork_marker}: {len(session.messages)} msgs, ~{session.token_count} tokens")

    def _get_session(self, session_name=None):
        if session_name:
            session = self.sessions.get(session_name)
            if not session:
                print(f"  [!] Session '{session_name}' not found.")
            return session
        return self.active_session


# --- Main demo ---

def main():
    print("=" * 60)
    print("M26 Lab — Session Management with Fork")
    print("=" * 60)

    mgr = SessionManager()

    # --- Create a session ---
    print("\n--- Step 1: Create a named session ---")
    mgr.create_session(
        "ucc-support-main",
        system_prompt="You are a UCC filing support agent. Help customers with filing lookups, risk checks, and refund requests."
    )

    # --- Add messages ---
    print("\n--- Step 2: Simulate a conversation ---")
    mgr.add_message("user", "I need to look up filing UCC-2024-NY-0012847 for Greenfield Logistics.")
    mgr.add_message("assistant", "I'll look that up for you. Let me search our filing database.")
    mgr.add_message("assistant", "Found it. Filing UCC-2024-NY-0012847 is Active. Debtor: Greenfield Logistics LLC. Secured Party: Atlantic Capital Partners. Expires 2029-03-15.")
    mgr.add_message("user", "What's their risk profile?")
    mgr.add_message("assistant", "Greenfield Logistics LLC has a LOW risk score of 0.35. No prior defaults, active 5+ years, single active lien.")
    mgr.add_message("user", "Now I want to explore what happens if we add a second lien.")

    # --- Fork for what-if analysis ---
    print("\n--- Step 3: Fork session for what-if analysis ---")
    mgr.fork_session("ucc-support-main", "ucc-support-what-if-second-lien")

    # Add messages to the fork (does NOT affect main)
    mgr.add_message("user", "Hypothetically, if Greenfield takes on a second lien from Pacific Trust, what happens to risk?", session_name="ucc-support-what-if-second-lien")
    mgr.add_message("assistant", "Adding a second lien would increase the risk score from 0.35 to approximately 0.58 (MEDIUM). Two concurrent liens raise subordination concerns.", session_name="ucc-support-what-if-second-lien")

    # Main session is unaffected
    print("\n--- Step 4: Verify isolation ---")
    main_session = mgr.sessions["ucc-support-main"]
    fork_session = mgr.sessions["ucc-support-what-if-second-lien"]
    print(f"  Main session messages: {len(main_session.messages)}")
    print(f"  Fork session messages: {len(fork_session.messages)}")
    print(f"  Isolation verified: {len(fork_session.messages) > len(main_session.messages)}")

    # --- Stale context detection ---
    print("\n--- Step 5: Stale context detection ---")
    # Check with tight limits to trigger staleness
    mgr.is_context_stale("ucc-support-main", max_age_minutes=30, max_token_pct=0.001)

    # Check with normal limits
    mgr.is_context_stale("ucc-support-main", max_age_minutes=30, max_token_pct=0.9)

    # --- Add more messages to trigger compaction ---
    print("\n--- Step 6: Context compaction ---")
    for i in range(5):
        mgr.add_message("user", f"Follow-up question #{i+1} about UCC filings and compliance requirements for multi-state entities.", session_name="ucc-support-main")
        mgr.add_message("assistant", f"Here is detailed answer #{i+1} covering jurisdictional rules, continuation statements, and amendment procedures.", session_name="ucc-support-main")

    print(f"\n  Before compaction: {len(mgr.sessions['ucc-support-main'].messages)} messages")
    mgr.compact_session("ucc-support-main", keep_recent=4)

    # --- List all sessions ---
    print("\n--- Step 7: List all sessions ---")
    mgr.list_sessions()

    print(f"\n{'='*60}")
    print("Key Takeaways")
    print(f"{'='*60}")
    print("""
    1. Named sessions: Create, resume, and manage by name
    2. fork_session: Branch for what-if analysis without polluting main context
    3. Stale detection: Warn when context is old or overfull
    4. Compaction: Summarize old messages to reclaim context budget
    5. Isolation: Fork changes never affect the parent session
    """)

    print("[OK] Lab Step 3 complete — Session management with fork\n")


if __name__ == "__main__":
    main()
