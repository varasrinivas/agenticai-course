"""
M00B Lab - Step 1: Raw OpenAI SDK Tool-Use Loop — SOLUTION
===========================================================
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

# ---- Tool implementation (plain Python) ----
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


# ---- Tool schema (OpenAI function-calling format) ----
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


# ---- The loop ----
def run_agent(user_message: str) -> str:
    messages = [{"role": "user", "content": user_message}]
    while True:
        try:
            resp = client.chat.completions.create(
                model="mistral",
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )
        except Exception as e:
            return f"API error: {e} (is Ollama running? ollama serve)"

        msg = resp.choices[0].message

        # Did the model finish?
        if not msg.tool_calls:
            return msg.content

        # The model requested tool calls — dispatch each one.
        messages.append(msg)
        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments)  # arguments is a JSON string
            if tc.function.name == "get_time":
                result_text = get_time(args["city"])
            else:
                result_text = f"Unknown tool: {tc.function.name}"
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result_text,
            })
        # Loop back — the model reads the tool result and answers


if __name__ == "__main__":
    print(run_agent("What time is it in Tokyo right now?"))
