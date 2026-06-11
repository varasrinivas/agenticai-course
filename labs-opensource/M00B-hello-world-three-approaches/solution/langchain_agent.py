"""
M00B Lab - Step 3: LangChain Agent — SOLUTION
==============================================
Run: python langchain_agent.py
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from langchain_community.chat_models import ChatOllama
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

TIMEZONES = {
    "new york": "America/New_York",
    "london": "Europe/London",
    "tokyo": "Asia/Tokyo",
    "sydney": "Australia/Sydney",
    "san francisco": "America/Los_Angeles",
}


# ---- Tool (docstring becomes the schema description) ----
@tool
def get_time(city: str) -> str:
    """Get the current local time in a major city such as Tokyo or London."""
    tz_name = TIMEZONES.get(city.lower())
    if tz_name is None:
        return f"Unknown city: {city}. Known cities: {', '.join(TIMEZONES)}."
    now = datetime.now(ZoneInfo(tz_name))
    return now.strftime("%H:%M on %A, %d %b %Y")


# ---- LLM (ChatOllama = local Mistral) ----
llm = ChatOllama(model="mistral")
tools = [get_time]

# ---- Prompt (system + human + scratchpad placeholder) ----
prompt = ChatPromptTemplate.from_messages([
    ("system", "You help users find the current local time in any city. Always use the get_time tool."),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad"),  # LangChain injects tool call history here
])

# ---- Agent = prompt | llm | tool dispatcher ----
agent = create_openai_tools_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools, verbose=False)

result = executor.invoke({"input": "What time is it in Tokyo right now?"})
print(result["output"])
