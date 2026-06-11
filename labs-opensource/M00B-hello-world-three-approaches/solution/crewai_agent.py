"""
M00B Lab - Step 2: CrewAI Agent — SOLUTION (Python only)
=========================================================
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


# ---- Tool (docstring becomes the tool description) ----
@tool("Get City Time")
def get_time(city: str) -> str:
    """Get the current local time in a major city such as Tokyo or London."""
    tz_name = TIMEZONES.get(city.lower())
    if tz_name is None:
        return f"Unknown city: {city}. Known cities: {', '.join(TIMEZONES)}."
    now = datetime.now(ZoneInfo(tz_name))
    return now.strftime("%H:%M on %A, %d %b %Y")


# ---- Agent (role + goal + tool list) ----
time_agent = Agent(
    role="World Clock Assistant",
    goal="Answer natural-language questions about the current time in any major city.",
    backstory="You help travellers and remote teams find the local time anywhere in the world.",
    tools=[get_time],
    llm="ollama/mistral",   # LiteLLM format: provider/model
    verbose=False,
)

# ---- Task ----
task = Task(
    description="What time is it in Tokyo right now?",
    expected_output="The current local time in Tokyo, including the day of the week.",
    agent=time_agent,
)

# ---- Crew (orchestration) ----
crew = Crew(agents=[time_agent], tasks=[task], verbose=False)
result = crew.kickoff()
print(result)
