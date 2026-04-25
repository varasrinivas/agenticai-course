"""
M26 Lab — Step 3: Session Management with Fork

Sessions allow an agent to persist conversation state across interactions
and branch into parallel explorations without polluting the main context.

YOUR TASK: Fill in the TODO sections to implement session management.

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
        # TODO: Implement session creation
        #
        # 1. Check if a session with this name already exists
        #    - If yes, print a warning and return the existing session
        # 2. Create a new Session object with the given name and system_prompt
        # 3. Store it in self.sessions[name]
        # 4. Set self.active_session to the new session
        # 5. Print the session name and system prompt (first 60 chars)
        # 6. Return the session

        pass  # <-- Replace this with your implementation

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

        # TODO: Implement message addition with token tracking
        #
        # 1. Create a message dict with role, content, and timestamp
        # 2. Append it to session.messages
        # 3. Estimate tokens: len(content) // 4
        # 4. Add estimated tokens to session.token_count
        # 5. Update session.last_active to datetime.now()
        # 6. Print the role and first 60 chars of content
        # 7. Print current token usage: f"      Tokens: ~{session.token_count}/{session.max_tokens}"
        # 8. If token usage > 80% of max_tokens, print a warning
        # 9. Return the message

        pass  # <-- Replace this with your implementation

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
        # TODO: Implement session forking
        #
        # 1. Check that source_name exists in self.sessions (print error if not)
        # 2. Check that fork_name doesn't already exist (print error if it does)
        # 3. Get the source session
        # 4. Create a new Session with fork_name, source's system_prompt, parent_name=source_name
        # 5. Deep copy: forked.messages = copy.deepcopy(source.messages)
        # 6. Copy: forked.token_count = source.token_count
        # 7. Deep copy: forked.metadata = copy.deepcopy(source.metadata)
        # 8. Store in self.sessions[fork_name]
        # 9. Print the fork details (source -> fork, message count, token count)
        # 10. Return the forked session

        pass  # <-- Replace this with your implementation

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

        # TODO: Implement stale context detection
        #
        # 1. Create a reasons list (empty)
        # 2. Check age: if (datetime.now() - session.last_active) > timedelta(minutes=max_age_minutes)
        #    - Add a reason string with the age and limit
        # 3. Check token usage: if (session.token_count / session.max_tokens) > max_token_pct
        #    - Add a reason string with the usage percentage and limit
        # 4. is_stale = len(reasons) > 0
        # 5. If stale, print the session name and each reason
        # 6. If not stale, print "[OK] Session '{name}' is fresh"
        # 7. Return is_stale

        pass  # <-- Replace this with your implementation

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

        # TODO: Implement context compaction
        #
        # 1. Save old_count = len(session.messages) and old_tokens = session.token_count
        # 2. Split messages: to_summarize = session.messages[:-keep_recent], recent = session.messages[-keep_recent:]
        # 3. Build summary_parts: for each msg in to_summarize, create f"[{msg['role']}] {msg['content'][:40]}..."
        # 4. Create a summary message dict with:
        #    - role: "system"
        #    - content: f"[Compacted summary of {len(to_summarize)} earlier messages]\n" + "\n".join(summary_parts)
        #    - timestamp: datetime.now().isoformat()
        #    - is_summary: True
        # 5. Replace session.messages with [summary] + recent
        # 6. Recalculate token_count: sum(len(m["content"]) // 4 for m in session.messages)
        # 7. Print before/after message count and token count

        pass  # <-- Replace this with your implementation

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
    main_session = mgr.sessions.get("ucc-support-main")
    fork_session = mgr.sessions.get("ucc-support-what-if-second-lien")
    if main_session and fork_session:
        print(f"  Main session messages: {len(main_session.messages)}")
        print(f"  Fork session messages: {len(fork_session.messages)}")
        print(f"  Isolation verified: {len(fork_session.messages) > len(main_session.messages)}")
    else:
        print("  [!] Sessions not found — check your create_session and fork_session implementations")

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

    main_session = mgr.sessions.get("ucc-support-main")
    if main_session:
        print(f"\n  Before compaction: {len(main_session.messages)} messages")
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
