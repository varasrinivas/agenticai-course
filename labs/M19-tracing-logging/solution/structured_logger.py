"""
M19 Lab — Structured Logger (Solution)
=======================================
Complete JSON structured logger with PII scrubbing.

Usage:
    python structured_logger.py
"""

import json
import re
import sys
from datetime import datetime, timezone
from typing import Optional


# =============================================================================
# PII SCRUBBER
# =============================================================================

PII_PATTERNS = {
    "ssn": r"\b\d{3}-?\d{2}-?\d{4}\b",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "phone": r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
}

REDACTED = "[REDACTED]"


def scrub_pii(data) -> any:
    """Recursively scrub PII from strings, dicts, and lists."""
    if isinstance(data, str):
        result = data
        for pattern in PII_PATTERNS.values():
            result = re.sub(pattern, REDACTED, result)
        return result
    elif isinstance(data, dict):
        return {k: scrub_pii(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [scrub_pii(item) for item in data]
    else:
        return data


# =============================================================================
# STRUCTURED LOGGER
# =============================================================================

class StructuredLogger:
    """JSON structured logger with automatic PII scrubbing."""

    LEVELS = {"DEBUG": 10, "INFO": 20, "WARN": 30, "ERROR": 40}

    def __init__(self, service_name: str = "agent", min_level: str = "DEBUG"):
        self.service_name = service_name
        self.min_level = min_level
        self.logs: list[dict] = []

    def log(self, level: str, message: str, trace_id: Optional[str] = None,
            span_id: Optional[str] = None, **kwargs) -> Optional[dict]:
        """Output a structured JSON log line."""
        if self.LEVELS.get(level, 0) < self.LEVELS.get(self.min_level, 0):
            return None

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "service": self.service_name,
            "message": message,
            "trace_id": trace_id,
            "span_id": span_id,
            **kwargs
        }

        # Remove None values
        entry = {k: v for k, v in entry.items() if v is not None}

        # Scrub PII
        entry = scrub_pii(entry)

        print(json.dumps(entry))
        self.logs.append(entry)
        return entry

    def log_llm_call(self, model: str, input_tokens: int, output_tokens: int,
                     duration_ms: float, trace_id: str = None,
                     span_id: str = None) -> Optional[dict]:
        """Log an LLM API call with token counts and latency."""
        return self.log(
            "INFO",
            f"LLM call to {model} completed",
            trace_id=trace_id,
            span_id=span_id,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            duration_ms=duration_ms,
            event_type="llm_call"
        )

    def log_tool_call(self, tool_name: str, tool_input: dict,
                      tool_output: dict, duration_ms: float,
                      trace_id: str = None, span_id: str = None) -> Optional[dict]:
        """Log a tool execution with input/output."""
        return self.log(
            "INFO",
            f"Tool '{tool_name}' executed",
            trace_id=trace_id,
            span_id=span_id,
            tool_name=tool_name,
            tool_input=scrub_pii(tool_input),
            tool_output=scrub_pii(tool_output),
            duration_ms=duration_ms,
            event_type="tool_call"
        )

    def log_error(self, error: Exception, trace_id: str = None,
                  span_id: str = None, **kwargs) -> Optional[dict]:
        """Log an error with exception details."""
        return self.log(
            "ERROR",
            str(error),
            trace_id=trace_id,
            span_id=span_id,
            error_type=type(error).__name__,
            event_type="error",
            **kwargs
        )


# =============================================================================
# SELF-TEST
# =============================================================================

def self_test():
    """Test structured logging and PII scrubbing."""
    print("=" * 60)
    print("M19 Structured Logger — Self-Test")
    print("=" * 60)

    # --- Test PII scrubbing ---
    print("\n--- PII Scrubbing Tests ---\n")

    test_cases = [
        ("SSN in text", "Customer SSN is 123-45-6789, please verify"),
        ("Email in text", "Contact john.doe@example.com for details"),
        ("Phone in text", "Call (555) 123-4567 for support"),
        ("Multiple PII", "SSN: 987-65-4321, email: jane@test.com, phone: 555-987-6543"),
        ("Nested dict", {"name": "John", "ssn": "111-22-3333", "email": "john@test.com"}),
        ("List with PII", ["Call 555-111-2222", "Email: test@test.com"]),
        ("No PII", "UCC filing #12345 for Acme Corp in New York"),
    ]

    for label, data in test_cases:
        result = scrub_pii(data)
        print(f"  {label}:")
        print(f"    Input:  {data}")
        print(f"    Output: {result}")
        print()

    # --- Test Structured Logger ---
    print("\n--- Structured Logger Tests ---\n")

    logger = StructuredLogger(service_name="ucc_agent")

    logger.log("INFO", "Agent started", trace_id="trace_001")

    logger.log_llm_call(
        model="claude-sonnet-4-20250514",
        input_tokens=350,
        output_tokens=120,
        duration_ms=823.5,
        trace_id="trace_001",
        span_id="span_001"
    )

    logger.log_tool_call(
        tool_name="search_filings",
        tool_input={"debtor_name": "John Doe", "ssn": "123-45-6789"},
        tool_output={"results": [{"filing": "UCC-001", "debtor": "John Doe"}]},
        duration_ms=45.2,
        trace_id="trace_001",
        span_id="span_002"
    )

    try:
        raise ValueError("API rate limit exceeded")
    except Exception as e:
        logger.log_error(e, trace_id="trace_001", span_id="span_003")

    logger = StructuredLogger(service_name="ucc_agent", min_level="WARN")
    result = logger.log("DEBUG", "This should be filtered out")
    assert result is None, "DEBUG should be filtered when min_level is WARN"
    print("\n(DEBUG log correctly filtered by min_level=WARN)")

    print(f"\nAll structured logger tests passed!")


if __name__ == "__main__":
    self_test()
