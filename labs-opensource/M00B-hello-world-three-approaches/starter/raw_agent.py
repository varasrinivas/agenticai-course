"""
M00B Lab - Step 1: Raw OpenAI SDK Tool-Use Loop
================================================
The tool and its schema are provided. You implement the agent loop.
Run: python raw_agent.py
"""

import json
from datetime import datetime
from zoneinfo import ZoneInfo
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:11434/v1",  # Ollama local endpoint
    api_key="ollama",                      # required by SDK but ignored by Ollama
)

# ---- Tool implementation (plain Python — COMPLETE) ----
TIMEZONES = {
    "new york": "America/New_York",
    "london": "Europe/London",
    "tokyo": "Asia/Tokyo",
    "sydney": "Australia/Sydney",
    "san francisco": "America/Los_Angeles",
}


def get_time(city: str) -> str:
    tz_name = TIMEZONES.get(city.lower())
    if tz_name is None:
        return f"Unknown city: {city}. Known cities: {', '.join(TIMEZONES)}."
    now = datetime.now(ZoneInfo(tz_name))
    return now.strftime("%H:%M on %A, %d %b %Y")


# ---- Tool schema (OpenAI function-calling format — COMPLETE) ----
TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_time",
        "description": "Get the current local time in a major city.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name, e.g. Tokyo"}
            },
            "required": ["city"],
        },
    },
}]


# ---- The loop (YOUR JOB) ----
def run_agent(user_message: str) -> str:
    # TODO: Implement the tool-use loop.
    # 1. messages = [{"role": "user", "content": user_message}]
    # 2. Loop forever:
    #    a. resp = client.chat.completions.create(model="mistral", messages=messages,
    #                                             tools=TOOLS, tool_choice="auto")
    #    b. msg = resp.choices[0].message
    #    c. If msg.tool_calls is None → the model is done: return msg.content
    #    d. Otherwise: messages.append(msg), then for each tc in msg.tool_calls:
    #       - args = json.loads(tc.function.arguments)   # arguments is a JSON STRING
    #       - call get_time(args["city"]) if tc.function.name == "get_time",
    #         else produce an "Unknown tool" error string
    #       - messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
    #    e. Loop back — the model will read the tool result and answer (or call again)
    # Wrap the API call in try/except and return an error string on failure.
    pass  # Remove this line when you add your code


if __name__ == "__main__":
    print(run_agent("What time is it in Tokyo right now?"))
