"""
M06 Lab - Step 1: Parallel Tool Dispatch (Solution)
=====================================================
Complete solution: handling multiple tool_use blocks in a single response.
Claude requests tools in parallel when inputs are independent.

Usage:
    python parallel_tools.py
"""

import json
import time
from dotenv import load_dotenv

load_dotenv()

import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-20250514"


# =============================================================================
# MOCK DATA AND TOOL FUNCTIONS
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
# TOOL DEFINITIONS
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
# OBSERVATION HELPERS
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
# SOLUTION: The Parallel-Aware Agent Loop
# =============================================================================

def run_agent(user_message: str) -> str:
    """
    Run the agent loop with explicit parallel tool dispatch.

    WHY parallel matters: When Claude requests 3 weather lookups at once,
    a production system could execute them concurrently (e.g., asyncio.gather).
    Here we execute sequentially but track the parallel pattern -- the key
    insight is that ALL tool_use blocks in one response are independent.
    """
    observe("QUERY", user_message)

    # Initialize conversation memory
    messages = [{"role": "user", "content": user_message}]
    total_tool_calls = 0

    # === THE AGENT LOOP ===
    turn = 0
    while turn < MAX_TURNS:
        turn += 1
        observe("THINKING", f"Turn {turn} -- sending {len(messages)} message(s) to Claude...")

        # DECIDE: Ask Claude what to do next
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason == "tool_use":
            # ACT: Execute ALL tool calls from this response
            # WHY we collect them all: Claude emits multiple tool_use blocks
            # when the calls are independent. We process them all before
            # sending results back -- this is the parallel dispatch pattern.
            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
            tool_results = []

            for block in tool_use_blocks:
                observe_tool_call(block.name, block.input)

                # Execute the tool (with error handling for unknown tools)
                if block.name in TOOL_FUNCTIONS:
                    result = TOOL_FUNCTIONS[block.name](block.input)
                else:
                    result = {"error": f"Unknown tool: {block.name}"}

                observe_tool_result(block.name, result)

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })

            # Track parallel tool call count for this turn
            parallel_count = len(tool_use_blocks)
            total_tool_calls += parallel_count
            print(f"\n[PARALLEL] Processed {parallel_count} tool calls in this turn")

            # OBSERVE: Add assistant message + tool results to memory
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})

        elif response.stop_reason == "end_turn":
            # Claude is done -- extract text
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text

            print(f"\n[SUMMARY] Total tool calls: {total_tool_calls}")
            observe("RESPONSE", final_text)
            return final_text

        else:
            observe("WARNING", f"Unexpected stop reason: {response.stop_reason}")
            return "Agent stopped unexpectedly."

    observe("ERROR", f"Agent exceeded maximum turns ({MAX_TURNS})")
    return "Error: Agent exceeded maximum number of turns."


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M06 Lab - Step 1: Parallel Tool Dispatch (SOLUTION)")
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
