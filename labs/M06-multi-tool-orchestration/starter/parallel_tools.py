"""
M06 Lab - Step 1: Parallel Tool Dispatch (Starter)
====================================================
Build an agent that handles MULTIPLE tool_use blocks in a single response.
Claude can request several tools at once -- your code must process them all
and send all results back together.

Usage:
    python parallel_tools.py
"""

import json
import time
from dotenv import load_dotenv

load_dotenv()

import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"


# =============================================================================
# MOCK DATA AND TOOL FUNCTIONS (complete -- do not modify)
# =============================================================================

WEATHER_DATA = {
    "new york": {"temp_f": 72, "condition": "Partly Cloudy", "humidity": 65},
    "london": {"temp_f": 58, "condition": "Rainy", "humidity": 80},
    "tokyo": {"temp_f": 85, "condition": "Sunny", "humidity": 45},
    "sydney": {"temp_f": 64, "condition": "Windy", "humidity": 55},
    "paris": {"temp_f": 68, "condition": "Overcast", "humidity": 70},
}


def get_weather(city: str) -> dict:
    """Look up weather for a city. Returns weather data or an error."""
    city_lower = city.lower().strip()
    if city_lower in WEATHER_DATA:
        data = WEATHER_DATA[city_lower]
        return {"city": city, **data}
    return {"error": f"No weather data available for '{city}'. Available cities: {', '.join(WEATHER_DATA.keys())}"}


def calculate(expression: str) -> dict:
    """Safely evaluate a math expression."""
    try:
        allowed = set("0123456789+-*/.(). ")
        if not all(c in allowed for c in expression):
            return {"error": f"Invalid characters in expression: {expression}"}
        result = eval(expression)  # Safe because we validated characters
        return {"expression": expression, "result": round(result, 6)}
    except Exception as e:
        return {"error": f"Calculation failed: {str(e)}"}


def get_time(timezone: str) -> dict:
    """Return current time for a timezone (mock)."""
    MOCK_TIMES = {
        "EST": "2024-03-15 14:30:00 EST",
        "PST": "2024-03-15 11:30:00 PST",
        "UTC": "2024-03-15 19:30:00 UTC",
        "JST": "2024-03-16 04:30:00 JST",
        "GMT": "2024-03-15 19:30:00 GMT",
    }
    tz = timezone.upper().strip()
    if tz in MOCK_TIMES:
        return {"timezone": tz, "current_time": MOCK_TIMES[tz]}
    return {"error": f"Unknown timezone: {timezone}. Available: {', '.join(MOCK_TIMES.keys())}"}


# =============================================================================
# TOOL DEFINITIONS (complete -- do not modify)
# =============================================================================

TOOLS = [
    {
        "name": "get_weather",
        "description": (
            "Get current weather data for a city. Returns temperature (Fahrenheit), "
            "condition, and humidity."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city name, e.g. 'Tokyo' or 'New York'",
                }
            },
            "required": ["city"],
        },
    },
    {
        "name": "calculate",
        "description": (
            "Evaluate a mathematical expression. Supports +, -, *, /, and parentheses. "
            "Use this for any math calculations the user asks about."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The math expression to evaluate, e.g. '15 * 340 / 100'",
                }
            },
            "required": ["expression"],
        },
    },
    {
        "name": "get_time",
        "description": (
            "Get the current time in a given timezone. "
            "Supported timezones: EST, PST, UTC, JST, GMT."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "The timezone abbreviation, e.g. 'EST', 'JST', 'UTC'",
                }
            },
            "required": ["timezone"],
        },
    },
]

# Dispatch map: tool name -> function that executes it
TOOL_FUNCTIONS = {
    "get_weather": lambda args: get_weather(args["city"]),
    "calculate": lambda args: calculate(args["expression"]),
    "get_time": lambda args: get_time(args["timezone"]),
}

MAX_TURNS = 10

SYSTEM_PROMPT = """\
You are a helpful assistant with access to three tools:
- get_weather: look up current weather for a city
- calculate: evaluate math expressions
- get_time: get the current time in a timezone

When the user asks about multiple things at once, call ALL relevant tools
in a single response (parallel tool use). Do not call them one at a time
when they are independent of each other.

Always explain the results in clear, natural language after receiving tool results.
"""


# =============================================================================
# OBSERVATION HELPERS (complete -- do not modify)
# =============================================================================

def observe(label: str, message: str) -> None:
    """Print a labeled observation line."""
    print(f"\n{'=' * 60}")
    print(f"[{label}] {message}")
    print(f"{'=' * 60}")


def observe_tool_call(tool_name: str, tool_input: dict) -> None:
    """Log a tool call."""
    print(f"\n{'─' * 60}")
    print(f"[USING TOOL] {tool_name}")
    print(f"[INPUT]      {json.dumps(tool_input, indent=2)}")
    print(f"{'─' * 60}")


def observe_tool_result(tool_name: str, result: dict) -> None:
    """Log a tool result."""
    print(f"\n{'─' * 60}")
    print(f"[TOOL RESULT] {tool_name} -> {json.dumps(result)}")
    print(f"{'─' * 60}")


# =============================================================================
# YOUR CODE: Implement the parallel-aware agent loop
# =============================================================================

def run_agent(user_message: str) -> str:
    """
    Run the agent loop with explicit parallel tool dispatch.

    The pattern:
        1. Send messages to Claude (with tools available)
        2. If stop_reason == "tool_use": find ALL tool_use blocks, execute them,
           count how many ran in parallel, send ALL results back at once
        3. If stop_reason == "end_turn": return the final text
        4. Repeat until done or MAX_TURNS exceeded

    Returns Claude's final text response.
    """
    observe("QUERY", user_message)

    # ------------------------------------------------------------------
    # TODO 1: Initialize messages and turn tracking
    #   messages = [{"role": "user", "content": user_message}]
    #   total_tool_calls = 0
    # ------------------------------------------------------------------
    messages = [{"role": "user", "content": user_message}]
    total_tool_calls = 0

    turn = 0
    while turn < MAX_TURNS:
        turn += 1
        observe("THINKING", f"Turn {turn} -- sending {len(messages)} message(s) to Claude...")

        # --------------------------------------------------------------
        # TODO 2: Call the Claude API with tools
        #   response = client.messages.create(
        #       model=MODEL, max_tokens=1024, system=SYSTEM_PROMPT,
        #       tools=TOOLS, messages=messages,
        #   )
        # --------------------------------------------------------------
        pass

        # --------------------------------------------------------------
        # TODO 3: Handle stop_reason == "tool_use" with PARALLEL dispatch
        #   - Collect ALL tool_use blocks from response.content
        #   - Log each one with observe_tool_call
        #   - Execute each tool using TOOL_FUNCTIONS[block.name](block.input)
        #   - Log each result with observe_tool_result
        #   - Print how many tool calls were processed in this turn:
        #     print(f"\n[PARALLEL] Processed {count} tool calls in this turn")
        #   - Build tool_results list with:
        #     {"type": "tool_result", "tool_use_id": block.id,
        #      "content": json.dumps(result)}
        #   - Append assistant message and tool results to messages
        #   - Update total_tool_calls
        #
        # KEY INSIGHT: All tool_use blocks in a single response are
        # INDEPENDENT -- Claude requested them in parallel because their
        # inputs don't depend on each other's outputs.
        # --------------------------------------------------------------
        pass

        # --------------------------------------------------------------
        # TODO 4: Handle stop_reason == "end_turn"
        #   - Extract text from response.content
        #   - Print summary: f"[SUMMARY] Total tool calls: {total_tool_calls}"
        #   - observe("RESPONSE", final_text)
        #   - Return final_text
        # --------------------------------------------------------------
        pass

    observe("ERROR", f"Agent exceeded maximum turns ({MAX_TURNS})")
    return "Error: Agent exceeded maximum number of turns."


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M06 Lab - Step 1: Parallel Tool Dispatch")
    print("=" * 60)

    # Test 1: Parallel weather lookups (3 cities)
    print("\n\n>>> Test 1: Parallel weather lookups (3 cities)")
    result1 = run_agent("What's the weather in Tokyo, New York, and London?")
    print(f"\nFINAL ANSWER: {result1}")

    # Test 2: Parallel across different tools
    print("\n\n>>> Test 2: Parallel across different tools")
    result2 = run_agent("What's the weather in Paris and what time is it in EST?")
    print(f"\nFINAL ANSWER: {result2}")

    # Test 3: Parallel calculate calls
    print("\n\n>>> Test 3: Parallel calculate calls")
    result3 = run_agent("What is 25 * 4 and what is 100 / 3?")
    print(f"\nFINAL ANSWER: {result3}")
