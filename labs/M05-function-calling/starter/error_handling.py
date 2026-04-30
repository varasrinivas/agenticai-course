"""
M05 Lab - Step 3: Error Handling and Edge Cases (Starter)
==========================================================
Make the multi-tool agent robust: handle API errors, unknown tools,
tool execution failures, and max-turns timeouts gracefully.

The key insight: when a tool fails, send the error BACK to Claude as a
tool_result. Claude can then explain the problem to the user instead
of the whole agent crashing.

Usage:
    python error_handling.py
"""

import json
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

Use the appropriate tool(s) to answer the user's questions. If a tool returns
an error, explain the problem to the user in plain language and suggest
alternatives if possible.
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


def observe_tool_result(result: dict) -> None:
    """Log a tool result."""
    print(f"\n{'─' * 60}")
    print(f"[TOOL RESULT]")
    print(json.dumps(result, indent=2))
    print(f"{'─' * 60}")


# =============================================================================
# YOUR CODE: Implement the error-handling agent loop
# =============================================================================

def run_agent_safe(user_message: str) -> str:
    """
    Run the multi-tool agent loop with comprehensive error handling.

    Error handling layers:
        1. API call errors (network, auth, rate limits)
        2. Unknown tool names (Claude hallucinates a tool)
        3. Tool execution failures (exceptions inside tool functions)
        4. Max turns exceeded (infinite loop protection)

    When a tool fails, send the error back as a tool_result so Claude
    can explain the problem gracefully instead of the agent crashing.

    Returns Claude's final text response, or an error message.
    """
    observe("QUERY", user_message)

    messages = [{"role": "user", "content": user_message}]

    turn = 0
    while turn < MAX_TURNS:
        turn += 1
        observe("THINKING", f"Turn {turn} of {MAX_TURNS}...")

        # --------------------------------------------------------------
        # TODO 1: Make the API call inside a try/except
        #   try:
        #       response = client.messages.create(...)
        #   except anthropic.APIError as e:
        #       observe("API ERROR", str(e))
        #       return f"Error: API call failed — {e}"
        #
        # This catches network errors, authentication failures,
        # rate limits, and other API-level problems.
        # --------------------------------------------------------------
        response = None  # Replace with your try/except API call
        pass

        # --------------------------------------------------------------
        # TODO 2: Handle stop_reason == "tool_use" with error protection
        #   For each tool_use block in response.content:
        #
        #   a) VALIDATE: Check if block.name is in TOOL_FUNCTIONS
        #      If not: result = {"error": f"Unknown tool: {block.name}"}
        #      (This handles the case where Claude asks for a tool
        #       that doesn't exist)
        #
        #   b) EXECUTE with try/except:
        #      try:
        #          result = TOOL_FUNCTIONS[block.name](block.input)
        #      except Exception as e:
        #          result = {"error": f"Tool '{block.name}' failed: {str(e)}"}
        #      (This handles crashes inside tool functions)
        #
        #   c) ALWAYS send the result back as a tool_result message,
        #      even if it contains an error. This lets Claude recover
        #      and explain the problem to the user.
        #
        #   Don't forget to:
        #   - Log with observe_tool_call and observe_tool_result
        #   - Append assistant message and tool results to messages
        # --------------------------------------------------------------
        pass

        # --------------------------------------------------------------
        # TODO 3: Handle stop_reason == "end_turn"
        #   Extract text from response.content and return it.
        # --------------------------------------------------------------
        pass

        # --------------------------------------------------------------
        # TODO 4: Handle unexpected stop_reason
        #   observe("WARNING", f"Unexpected stop reason: {response.stop_reason}")
        #   return "Agent stopped unexpectedly."
        # --------------------------------------------------------------
        pass

    # ------------------------------------------------------------------
    # TODO 5: Max turns exceeded
    #   observe("ERROR", f"Agent exceeded maximum turns ({MAX_TURNS})")
    #   return "Error: Agent exceeded maximum number of turns."
    # ------------------------------------------------------------------
    return ""


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M05 Lab - Step 3: Error Handling and Edge Cases")
    print("=" * 60)

    # Test 1: Unknown city (tool returns error -> Claude explains)
    print("\n\n>>> Test 1: Unknown city")
    result1 = run_agent_safe("What's the weather in Atlantis?")
    print(f"\nFINAL ANSWER: {result1}")

    # Test 2: Division by zero (tool error -> Claude explains)
    print("\n\n>>> Test 2: Division by zero")
    result2 = run_agent_safe("Calculate 1/0")
    print(f"\nFINAL ANSWER: {result2}")

    # Test 3: Multi-tool with mixed results
    print("\n\n>>> Test 3: Multi-tool")
    result3 = run_agent_safe("What's the weather in Tokyo and calculate 25 * 4?")
    print(f"\nFINAL ANSWER: {result3}")

    # Test 4: Normal query (no errors)
    print("\n\n>>> Test 4: Normal query")
    result4 = run_agent_safe("What time is it in EST?")
    print(f"\nFINAL ANSWER: {result4}")
