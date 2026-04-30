"""
M19 Lab — Structured Logger (Starter)
======================================
Build a JSON structured logger with PII scrubbing. Every log line
is a valid JSON object that can be parsed by jq, Datadog, or any
log aggregator.

KEY CONCEPT: Unstructured logs ("INFO: called the API") are hard
to search, filter, and alert on. Structured logs (JSON objects with
consistent fields) let you query your logs like a database:
  jq 'select(.level == "ERROR" and .trace_id == "abc123")' logs.jsonl

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

# WHAT: A function that finds and redacts personally identifiable
#   information (PII) in log data — SSNs, emails, phone numbers.
# WHY:  Logs often contain user input that may include PII. Regulations
#   like HIPAA and GDPR require you to keep PII out of logs. A scrubber
#   applied at the logging layer catches PII before it reaches storage.
# GOTCHA: Regex-based scrubbing is not perfect — it catches common
#   formats but can miss edge cases. For production, combine with a
#   dedicated PII detection library.

# Patterns to detect and redact
PII_PATTERNS = {
    # SSN: 123-45-6789 or 123456789
    "ssn": r"\b\d{3}-?\d{2}-?\d{4}\b",
    # Email: user@example.com
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    # US Phone: (123) 456-7890, 123-456-7890, 1234567890, +1-123-456-7890
    "phone": r"(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
}

REDACTED = "[REDACTED]"


def scrub_pii(data) -> any:
    """
    Recursively scrub PII from strings, dicts, and lists.

    Handles:
    - Strings: replace PII patterns with [REDACTED]
    - Dicts: scrub all values (keys are preserved)
    - Lists: scrub all elements
    - Other types: return unchanged
    """
    # TODO: Implement recursive PII scrubbing:
    #
    # 1. If data is a str:
    #    - For each pattern in PII_PATTERNS.values(), use re.sub()
    #      to replace matches with REDACTED
    #    - Return the scrubbed string
    #
    # 2. If data is a dict:
    #    - Return a new dict with the same keys but scrub_pii() applied
    #      to each value
    #
    # 3. If data is a list:
    #    - Return a new list with scrub_pii() applied to each element
    #
    # 4. Otherwise, return data unchanged
    pass


# =============================================================================
# STRUCTURED LOGGER
# =============================================================================

# WHAT: A logger that outputs one JSON object per log line, with
#   consistent fields (timestamp, level, message, trace_id, span_id)
#   plus arbitrary extra fields.
# WHY:  JSON log lines are machine-parseable. You can pipe them through
#   jq, ship them to Datadog/Splunk, or query them with SQL. Every
#   log line carries the trace_id so you can correlate logs with traces.
# GOTCHA: Always scrub PII before logging. The scrub_pii() call in
#   log() ensures no PII leaks even if the caller forgets.

class StructuredLogger:
    """JSON structured logger with automatic PII scrubbing."""

    # Log levels in order of severity
    LEVELS = {"DEBUG": 10, "INFO": 20, "WARN": 30, "ERROR": 40}

    def __init__(self, service_name: str = "agent", min_level: str = "DEBUG"):
        """
        Args:
            service_name: Name included in every log line for filtering
            min_level: Minimum log level to output (DEBUG, INFO, WARN, ERROR)
        """
        # TODO: Store service_name and min_level
        # Also initialize self.logs as an empty list to capture log entries
        pass

    def log(self, level: str, message: str, trace_id: Optional[str] = None,
            span_id: Optional[str] = None, **kwargs) -> Optional[dict]:
        """
        Output a structured JSON log line.

        Returns the log entry dict (for testing), or None if filtered by level.
        """
        # TODO:
        # 1. Check if the level is at or above min_level using self.LEVELS.
        #    If below, return None.
        # 2. Build a log entry dict with these fields:
        #    - "timestamp": current UTC time in ISO-8601 format
        #    - "level": the level string
        #    - "service": self.service_name
        #    - "message": the message
        #    - "trace_id": trace_id (if provided)
        #    - "span_id": span_id (if provided)
        #    - Plus any extra **kwargs
        # 3. Remove keys with None values from the entry
        # 4. Scrub PII from the entire entry using scrub_pii()
        # 5. Print the entry as a JSON string (json.dumps, no indent)
        # 6. Append the entry to self.logs
        # 7. Return the entry
        pass

    def log_llm_call(self, model: str, input_tokens: int, output_tokens: int,
                     duration_ms: float, trace_id: str = None,
                     span_id: str = None) -> Optional[dict]:
        """Log an LLM API call with token counts and latency."""
        # TODO: Call self.log() with level="INFO", a descriptive message,
        # and these extra fields: model, input_tokens, output_tokens,
        # total_tokens, duration_ms, event_type="llm_call"
        pass

    def log_tool_call(self, tool_name: str, tool_input: dict,
                      tool_output: dict, duration_ms: float,
                      trace_id: str = None, span_id: str = None) -> Optional[dict]:
        """Log a tool execution with input/output."""
        # TODO: Call self.log() with level="INFO", a descriptive message,
        # and these extra fields: tool_name, tool_input (scrubbed),
        # tool_output (scrubbed), duration_ms, event_type="tool_call"
        pass

    def log_error(self, error: Exception, trace_id: str = None,
                  span_id: str = None, **kwargs) -> Optional[dict]:
        """Log an error with exception details."""
        # TODO: Call self.log() with level="ERROR",
        # message = str(error),
        # error_type = type(error).__name__,
        # event_type = "error",
        # plus any extra **kwargs
        pass


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

    # Basic log
    logger.log("INFO", "Agent started", trace_id="trace_001")

    # LLM call log
    logger.log_llm_call(
        model="claude-sonnet-4-6",
        input_tokens=350,
        output_tokens=120,
        duration_ms=823.5,
        trace_id="trace_001",
        span_id="span_001"
    )

    # Tool call log with PII in input
    logger.log_tool_call(
        tool_name="search_filings",
        tool_input={"debtor_name": "John Doe", "ssn": "123-45-6789"},
        tool_output={"results": [{"filing": "UCC-001", "debtor": "John Doe"}]},
        duration_ms=45.2,
        trace_id="trace_001",
        span_id="span_002"
    )

    # Error log
    try:
        raise ValueError("API rate limit exceeded")
    except Exception as e:
        logger.log_error(e, trace_id="trace_001", span_id="span_003")

    # Filtered log (below min level)
    logger = StructuredLogger(service_name="ucc_agent", min_level="WARN")
    result = logger.log("DEBUG", "This should be filtered out")
    assert result is None, "DEBUG should be filtered when min_level is WARN"
    print("\n(DEBUG log correctly filtered by min_level=WARN)")

    print(f"\nAll structured logger tests passed!")


if __name__ == "__main__":
    self_test()
