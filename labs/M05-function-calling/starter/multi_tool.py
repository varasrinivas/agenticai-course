"""
M05 Lab - Step 2: Multi-Tool Agent Loop (Starter)
===================================================
Build the CORE PATTERN of every AI agent: the tool-use while loop.
Three tools, multiple turns, and the decide-act-observe-repeat cycle.

Usage:
    python multi_tool.py
"""

import json
from dotenv import load_dotenv

load_dotenv()

import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-20250514"


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

# Maximum turns to prevent infinite loops
MAX_TURNS = 10

# System prompt
SYSTEM_PROMPT = """\
You are a helpful assistant with access to three tools:
- get_weather: look up current weather for a city
- calculate: evaluate math expressions
- get_time: get the current time in a timezone

Use the appropriate tool(s) to answer the user's questions. You may use
multiple tools in a single response if needed. Always explain the results
in clear, natural language after receiving tool results.
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
# YOUR CODE: Implement the agent loop
# =============================================================================

def run_agent(user_message: str) -> str:
    """
    Run the multi-tool agent loop.

    The pattern:
        1. Send messages to Claude (with tools available)
        2. If stop_reason == "tool_use": execute ALL tool calls, send results back
        3. If stop_reason == "end_turn": return the final text
        4. Repeat until done or MAX_TURNS exceeded

    Returns Claude's final text response.
    """
    observe("QUERY", user_message)

    # ------------------------------------------------------------------
    # TODO 1: Initialize the messages list with the user's message
    #   messages = [{"role": "user", "content": user_message}]
    # ------------------------------------------------------------------
    pass

    # ------------------------------------------------------------------
    # TODO 2: Start the agent loop
    #   turn = 0
    #   while turn < MAX_TURNS:
    #       turn += 1
    #       observe("THINKING", f"Turn {turn}...")
    # ------------------------------------------------------------------
    pass

        # --------------------------------------------------------------
        # TODO 3: Call client.messages.create with:
        #   model=MODEL, max_tokens=1024, system=SYSTEM_PROMPT,
        #   tools=TOOLS, messages=messages
        # --------------------------------------------------------------
        pass

        # --------------------------------------------------------------
        # TODO 4: Handle stop_reason == "tool_use"
        #   - Loop through response.content
        #   - For each block where block.type == "tool_use":
        #       - Log with observe_tool_call
        #       - Execute TOOL_FUNCTIONS[block.name](block.input)
        #       - Log with observe_tool_result
        #       - Collect {"type": "tool_result", "tool_use_id": block.id,
        #                   "content": json.dumps(result)}
        #   - Append assistant message: {"role": "assistant", "content": response.content}
        #   - Append tool results: {"role": "user", "content": tool_results}
        #   - Continue the loop (Claude will see results on next turn)
        # --------------------------------------------------------------
        pass

        # --------------------------------------------------------------
        # TODO 5: Handle stop_reason == "end_turn"
        #   - Extract text from response.content (check hasattr(block, "text"))
        #   - observe("RESPONSE", final_text)
        #   - Return the final text
        # --------------------------------------------------------------
        pass

    # ------------------------------------------------------------------
    # TODO 6: If we exit the loop, return a max-turns error message
    #   observe("ERROR", f"Agent exceeded maximum turns ({MAX_TURNS})")
    #   return "Error: Agent exceeded maximum number of turns."
    # ------------------------------------------------------------------
    return ""


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M05 Lab - Step 2: Multi-Tool Agent Loop")
    print("=" * 60)

    # Test 1: Single tool (weather)
    print("\n\n>>> Test 1: Single tool (weather)")
    result1 = run_agent("What's the weather in Paris?")
    print(f"\nFINAL ANSWER: {result1}")

    # Test 2: Single tool (calculate)
    print("\n\n>>> Test 2: Single tool (calculate)")
    result2 = run_agent("What is 15% of 340?")
    print(f"\nFINAL ANSWER: {result2}")

    # Test 3: Multi-tool (weather + time)
    print("\n\n>>> Test 3: Multi-tool")
    result3 = run_agent("What's the weather in Tokyo and what time is it there?")
    print(f"\nFINAL ANSWER: {result3}")

    # Test 4: No tool needed
    print("\n\n>>> Test 4: No tool needed")
    result4 = run_agent("Hello, how are you?")
    print(f"\nFINAL ANSWER: {result4}")
