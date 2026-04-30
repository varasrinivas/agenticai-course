"""
M05 Lab - Step 1: Single Tool Call (Solution)
==============================================
Complete solution: define a weather tool, handle Claude's tool_use request,
execute the tool, send the result back, and return Claude's final response.

Usage:
    python single_tool.py
"""

import json
from dotenv import load_dotenv

load_dotenv()

import anthropic

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"


# =============================================================================
# MOCK DATA
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


# =============================================================================
# TOOL DEFINITION
# =============================================================================

WEATHER_TOOL = {
    "name": "get_weather",
    "description": (
        "Get current weather data for a city. Returns temperature (Fahrenheit), "
        "condition, and humidity. Use this when the user asks about weather."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "The city name to look up weather for, e.g. 'Tokyo' or 'New York'",
            }
        },
        "required": ["city"],
    },
}


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


def observe_tool_result(result: dict) -> None:
    """Log a tool result."""
    print(f"\n{'─' * 60}")
    print(f"[TOOL RESULT]")
    print(json.dumps(result, indent=2))
    print(f"{'─' * 60}")


# =============================================================================
# SOLUTION: run_single_tool
# =============================================================================

def run_single_tool(user_message: str) -> str:
    """
    Send a message to Claude with the weather tool available.
    If Claude wants to use the tool, execute it and send the result back.

    Returns Claude's final text response.
    """
    observe("QUERY", user_message)

    # Step 1: Call the API with the tool definition
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=[WEATHER_TOOL],
        messages=[{"role": "user", "content": user_message}],
    )

    # Step 2: If Claude didn't want to use a tool, return the text directly
    if response.stop_reason != "tool_use":
        final_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                final_text += block.text
        observe("RESPONSE", final_text)
        return final_text

    # Step 3: Find the tool_use block
    tool_block = None
    for block in response.content:
        if block.type == "tool_use":
            tool_block = block
            break

    if tool_block is None:
        return "Error: stop_reason was tool_use but no tool_use block found."

    # Step 4: Execute the tool and log it
    observe_tool_call(tool_block.name, tool_block.input)
    result = get_weather(tool_block.input["city"])
    observe_tool_result(result)

    # Step 5: Send the tool result back to Claude
    followup_response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=[WEATHER_TOOL],
        messages=[
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": response.content},
            {"role": "user", "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": json.dumps(result),
                }
            ]},
        ],
    )

    # Step 6: Extract and return Claude's final text
    final_text = ""
    for block in followup_response.content:
        if hasattr(block, "text"):
            final_text += block.text

    observe("RESPONSE", final_text)
    return final_text


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M05 Lab - Step 1: Single Tool Call (SOLUTION)")
    print("=" * 60)

    # Test 1: Known city
    print("\n\n>>> Test 1: Known city")
    result1 = run_single_tool("What's the weather in Tokyo?")
    print(f"\nFINAL ANSWER: {result1}")

    # Test 2: Unknown city (error case)
    print("\n\n>>> Test 2: Unknown city (error case)")
    result2 = run_single_tool("What's the weather in Atlantis?")
    print(f"\nFINAL ANSWER: {result2}")

    # Test 3: No tool needed
    print("\n\n>>> Test 3: No tool needed")
    result3 = run_single_tool("Hello! What can you help me with?")
    print(f"\nFINAL ANSWER: {result3}")
