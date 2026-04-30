"""
Common test utilities shared across labs.
This file is COMPLETE — import from here in your test code.

Usage:
    from shared.test_helpers import assert_valid_response, mock_claude_response, load_env
"""

import os
import json
import time
from pathlib import Path


def load_env():
    """Load environment variables from .env file in the labs root."""
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())


def assert_valid_response(response):
    """Assert that a Claude API response has the expected structure."""
    assert hasattr(response, "content"), "Response missing 'content' attribute"
    assert len(response.content) > 0, "Response content is empty"
    assert hasattr(response, "model"), "Response missing 'model' attribute"
    assert hasattr(response, "stop_reason"), "Response missing 'stop_reason' attribute"
    assert response.stop_reason in ("end_turn", "tool_use", "max_tokens"), \
        f"Unexpected stop_reason: {response.stop_reason}"


def get_text_content(response) -> str:
    """Extract text content from a Claude API response."""
    for block in response.content:
        if hasattr(block, "text"):
            return block.text
    return ""


def get_tool_use_blocks(response) -> list:
    """Extract tool_use blocks from a Claude API response."""
    return [block for block in response.content if block.type == "tool_use"]


def get_tool_use_by_name(response, tool_name: str):
    """Extract a specific tool_use block by tool name. Returns None if not found."""
    for block in response.content:
        if block.type == "tool_use" and block.name == tool_name:
            return block
    return None


def mock_claude_response(text: str = "This is a mock response.", stop_reason: str = "end_turn"):
    """Create a mock Claude response object for testing without API calls."""
    class MockBlock:
        def __init__(self, text):
            self.type = "text"
            self.text = text

    class MockUsage:
        def __init__(self):
            self.input_tokens = 25
            self.output_tokens = 15

    class MockResponse:
        def __init__(self, text, stop_reason):
            self.content = [MockBlock(text)]
            self.model = "claude-sonnet-4-6"
            self.stop_reason = stop_reason
            self.usage = MockUsage()

    return MockResponse(text, stop_reason)


def mock_tool_use_response(tool_name: str, tool_input: dict, tool_use_id: str = "toolu_mock_001"):
    """Create a mock Claude response with a tool_use block."""
    class MockToolBlock:
        def __init__(self, name, input_data, id):
            self.type = "tool_use"
            self.name = name
            self.input = input_data
            self.id = id

    class MockUsage:
        def __init__(self):
            self.input_tokens = 50
            self.output_tokens = 30

    class MockResponse:
        def __init__(self, tool_block):
            self.content = [tool_block]
            self.model = "claude-sonnet-4-6"
            self.stop_reason = "tool_use"
            self.usage = MockUsage()

    return MockResponse(MockToolBlock(tool_name, tool_input, tool_use_id))


def print_separator(title: str = ""):
    """Print a visual separator for lab output."""
    width = 60
    if title:
        padding = (width - len(title) - 2) // 2
        print(f"\n{'=' * padding} {title} {'=' * padding}")
    else:
        print(f"\n{'=' * width}")


def format_tokens(count: int) -> str:
    """Format token count with commas and cost estimate."""
    cost_per_million_input = 3.00  # Claude Sonnet pricing
    cost = (count / 1_000_000) * cost_per_million_input
    return f"{count:,} tokens (~${cost:.4f})"


def format_cost(input_tokens: int, output_tokens: int, model: str = "sonnet") -> str:
    """Calculate and format the cost of an API call."""
    pricing = {
        "sonnet": {"input": 3.00, "output": 15.00},
        "haiku": {"input": 0.25, "output": 1.25},
        "opus": {"input": 15.00, "output": 75.00},
    }
    rates = pricing.get(model, pricing["sonnet"])
    input_cost = (input_tokens / 1_000_000) * rates["input"]
    output_cost = (output_tokens / 1_000_000) * rates["output"]
    total = input_cost + output_cost
    return f"${total:.4f} ({input_tokens:,} in / {output_tokens:,} out)"


class CostTracker:
    """Track cumulative API costs across multiple calls in a lab session."""

    def __init__(self, model: str = "sonnet"):
        self.model = model
        self.calls = []

    def record(self, response):
        """Record token usage from a Claude API response."""
        if hasattr(response, "usage"):
            self.calls.append({
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "timestamp": time.time(),
            })

    @property
    def total_input_tokens(self) -> int:
        return sum(c["input_tokens"] for c in self.calls)

    @property
    def total_output_tokens(self) -> int:
        return sum(c["output_tokens"] for c in self.calls)

    @property
    def total_cost(self) -> float:
        pricing = {
            "sonnet": {"input": 3.00, "output": 15.00},
            "haiku": {"input": 0.25, "output": 1.25},
            "opus": {"input": 15.00, "output": 75.00},
        }
        rates = pricing.get(self.model, pricing["sonnet"])
        input_cost = (self.total_input_tokens / 1_000_000) * rates["input"]
        output_cost = (self.total_output_tokens / 1_000_000) * rates["output"]
        return input_cost + output_cost

    def summary(self) -> str:
        return (
            f"{len(self.calls)} API calls | "
            f"{self.total_input_tokens:,} in + {self.total_output_tokens:,} out | "
            f"${self.total_cost:.4f}"
        )


if __name__ == "__main__":
    # Quick self-test
    mock = mock_claude_response("Hello from mock!")
    assert_valid_response(mock)

    tool_mock = mock_tool_use_response("get_weather", {"city": "NYC"})
    assert tool_mock.stop_reason == "tool_use"
    assert get_tool_use_blocks(tool_mock)[0].name == "get_weather"

    tracker = CostTracker()
    tracker.record(mock)
    assert tracker.total_input_tokens == 25

    print("test_helpers.py: All self-tests passed")
