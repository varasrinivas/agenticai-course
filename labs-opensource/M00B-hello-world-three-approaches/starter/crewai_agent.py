"""
M00B Lab - Step 2: CrewAI Agent (Python only)
==============================================
The tool body is provided. You wire up the Agent, Task, and Crew.
Run: python crewai_agent.py
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from crewai import Agent, Task, Crew
from crewai.tools import tool

TIMEZONES = {
    "new york": "America/New_York",
    "london": "Europe/London",
    "tokyo": "Asia/Tokyo",
    "sydney": "Australia/Sydney",
    "san francisco": "America/Los_Angeles",
}


# TODO 1: Decorate this function with @tool("Get City Time").
# The DOCSTRING becomes the tool description the model sees — keep it descriptive.
def get_time(city: str) -> str:
    """Get the current local time in a major city such as Tokyo or London."""
    tz_name = TIMEZONES.get(city.lower())
    if tz_name is None:
        return f"Unknown city: {city}. Known cities: {', '.join(TIMEZONES)}."
    now = datetime.now(ZoneInfo(tz_name))
    return now.strftime("%H:%M on %A, %d %b %Y")


# TODO 2: Define the Agent.
# - role: "World Clock Assistant"
# - goal: answer natural-language questions about the current time in any major city
# - backstory: one sentence of persona
# - tools: [get_time]
# - llm: "ollama/mistral"   ← LiteLLM format: provider/model
# - verbose: False
time_agent = None  # Replace with your Agent(...)

# TODO 3: Define the Task.
# - description: "What time is it in Tokyo right now?"
# - expected_output: describe what a good answer contains (time + day of week)
# - agent: time_agent
task = None  # Replace with your Task(...)

# TODO 4: Create the Crew and kick it off.
# crew = Crew(agents=[...], tasks=[...], verbose=False)
# print(crew.kickoff())
