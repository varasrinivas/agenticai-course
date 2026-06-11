"""
M05 Lab: Tool Definitions + Mock Implementations (shared helper —
identical to starter version; tools are never the exercise here)
"""

import json

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a city. Returns temperature (Celsius), condition, and humidity.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name, e.g. 'Tokyo' or 'New York'"}
                },
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Evaluate a mathematical expression. Use for any math computation. Supports +, -, *, /, **, parentheses.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Math expression, e.g. '(15 * 7) + 23'"}
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "Get the current time in a specific timezone. Returns time in HH:MM format.",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {"type": "string", "description": "Timezone, e.g. 'US/Eastern', 'Asia/Tokyo', 'Europe/London'"}
                },
                "required": ["timezone"],
            },
        },
    },
]

MOCK_WEATHER = {
    "tokyo": {"temp": 22, "condition": "sunny", "humidity": 45},
    "london": {"temp": 14, "condition": "cloudy", "humidity": 72},
    "new york": {"temp": 28, "condition": "partly cloudy", "humidity": 60},
}

MOCK_TIMES = {"us/eastern": "14:30", "asia/tokyo": "03:30", "europe/london": "19:30"}


def run_tool(name: str, args: dict) -> str:
    """Execute a tool and return the result as a JSON string."""
    if name == "get_weather":
        city = args.get("city", "").lower()
        data = MOCK_WEATHER.get(city)
        if data:
            return json.dumps(data)
        return json.dumps({"error": f"City '{args.get('city')}' not found. Available: Tokyo, London, New York"})

    elif name == "calculate":
        expr = args.get("expression", "")
        try:
            allowed = set("0123456789+-*/.()% ")
            if not all(c in allowed for c in expr):
                return json.dumps({"error": f"Invalid characters in expression: {expr}"})
            result = eval(expr)  # safe because we validated characters above
            return json.dumps({"result": result})
        except Exception as e:
            return json.dumps({"error": f"Calculation failed: {e}"})

    elif name == "get_time":
        tz = args.get("timezone", "")
        time_str = MOCK_TIMES.get(tz.lower(), "12:00")
        return json.dumps({"timezone": tz, "time": time_str})

    return json.dumps({"error": f"Unknown tool: {name}"})
