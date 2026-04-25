"""
M02 Lab — Step 3: Context Window Budget Manager (Solution)
============================================================
Track token usage across a conversation and trim when needed.
"""
import tiktoken


class ContextBudgetManager:
    """Track and manage token usage within a context window."""

    def __init__(self, max_tokens: int = 1000):
        self.max_tokens = max_tokens
        self.messages: list[dict] = []
        self.total_tokens = 0
        self.encoding = tiktoken.get_encoding("cl100k_base")

    def _count_tokens(self, text: str) -> int:
        return len(self.encoding.encode(text))

    def add_message(self, role: str, content: str) -> dict:
        """Add a message and return token info."""
        token_count = self._count_tokens(content)
        self.messages.append({"role": role, "content": content, "tokens": token_count})
        self.total_tokens += token_count
        return {"tokens": token_count, "total": self.total_tokens, "max": self.max_tokens}

    def get_usage(self) -> dict:
        """Return current token usage stats."""
        return {
            "used": self.total_tokens,
            "max": self.max_tokens,
            "remaining": self.max_tokens - self.total_tokens,
            "percent": (self.total_tokens / self.max_tokens) * 100,
        }

    def would_fit(self, text: str) -> bool:
        """Check if new text would fit in remaining budget."""
        new_tokens = self._count_tokens(text)
        return (self.total_tokens + new_tokens) <= self.max_tokens

    def trim_oldest(self) -> int:
        """Remove oldest messages until under budget. Return count of messages removed."""
        removed = 0
        while self.total_tokens > self.max_tokens and self.messages:
            oldest = self.messages.pop(0)
            self.total_tokens -= oldest["tokens"]
            removed += 1
        return removed


if __name__ == "__main__":
    print("=== Context Window Budget Manager ===\n")
    mgr = ContextBudgetManager(max_tokens=1000)

    print("Adding messages to conversation...")
    sample_messages = [
        ("user", "What is machine learning?"),
        ("assistant", "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It focuses on developing algorithms that can access data, learn from it, and make predictions or decisions."),
        ("user", "Can you give me an example?"),
        ("assistant", "Sure! Consider email spam filtering. A machine learning model is trained on thousands of emails labeled as spam or not-spam. It learns patterns like certain keywords, sender addresses, or formatting tricks that indicate spam. When a new email arrives, the model uses these learned patterns to predict whether it's spam, without anyone having to write explicit rules for every possible spam message."),
    ]
    for i, (role, content) in enumerate(sample_messages, 1):
        try:
            info = mgr.add_message(role, content)
            preview = content[:40] + "..." if len(content) > 40 else content
            print(f'  [{i}] {role}: "{preview}" — {info["tokens"]} tokens ({info["total"]} / {info["max"]} used)')
        except Exception as e:
            print(f"  [{i}] [ERROR] {e}")

    print()
    try:
        usage = mgr.get_usage()
        print(f"Current usage: {usage['used']} / {usage['max']} tokens ({usage['percent']:.1f}%)")
        print(f"Remaining: {usage['remaining']} tokens")
    except Exception as e:
        print(f"[ERROR] {e}")

    print()
    print(f"Would a 500-token message fit? {mgr.would_fit('x ' * 250)}")
    print(f"Would a 900-token message fit? {mgr.would_fit('x ' * 450)}")

    print("\nSimulating context overflow...")
    print("  Adding 5 large messages (200 tokens each)...")
    for i in range(5):
        mgr.add_message("user", "This is a large padding message. " * 30)

    try:
        usage = mgr.get_usage()
        print(f"  Usage before trim: {usage['used']} / {usage['max']} tokens ({usage['percent']:.1f}%) — {'OVER BUDGET' if usage['used'] > usage['max'] else 'OK'}")
        removed = mgr.trim_oldest()
        usage = mgr.get_usage()
        print(f"  Trimming oldest messages...")
        print(f"  Usage after trim: {usage['used']} / {usage['max']} tokens ({usage['percent']:.1f}%)")
        print(f"  Removed {removed} messages to get back under budget.")
    except Exception as e:
        print(f"  [ERROR] {e}")
