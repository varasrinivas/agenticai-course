"""
M06 Lab - Step 1: Tools, Mocks, Dispatcher, Registry (COMPLETE)
================================================================
Five research tools. Imported by research_agent.py.
Run standalone to sanity-check: python tools_registry.py
"""

import json
import time

# ── Tool Schemas (OpenAI format) ──────────────────────────────
# NOTE how descriptions choreograph the chain: "Use after web_search",
# "Use after fetch_page" — the model learns the sequence from these.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Search the web for current information. Returns top 3 "
                "results with title, URL, and snippet. Use for recent "
                "events, factual questions, or general research."
            ),
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "Search query"}},
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_page",
            "description": (
                "Fetch the full text content of a web page by URL. "
                "Returns page text (max 5000 chars). Use after "
                "web_search to get full content from a result URL."
            ),
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string", "description": "Full URL to fetch"}},
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_text",
            "description": (
                "Summarize long text into key points (3-5 bullets). "
                "Use after fetch_page to condense page content."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to summarize"},
                    "max_points": {"type": "integer", "description": "Max bullet points (default 5)"},
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "format_citation",
            "description": (
                "Format a source as an academic citation. Use after "
                "summaries are ready to create proper references."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Article title"},
                    "url": {"type": "string", "description": "Source URL"},
                    "accessed_date": {"type": "string", "description": "e.g. '2025-01-15'"},
                },
                "required": ["title", "url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_to_file",
            "description": "Save content to a local file. Returns file path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Output filename"},
                    "content": {"type": "string", "description": "Content to save"},
                },
                "required": ["filename", "content"],
            },
        },
    },
]


# ── Mock Implementations (replace with real APIs in production) ──
def web_search(query: str) -> dict:
    time.sleep(0.2)  # simulate latency — makes parallel vs sequential measurable
    return {"results": [
        {"title": f"Result 1: {query}", "url": "https://example.com/1",
         "snippet": f"Overview of {query}..."},
        {"title": f"Result 2: {query}", "url": "https://example.com/2",
         "snippet": f"Developments in {query}..."},
        {"title": f"Result 3: {query}", "url": "https://broken.example.com/404",
         "snippet": f"Deep dive into {query}..."},
    ]}


def fetch_page(url: str) -> dict:
    time.sleep(0.3)
    if "broken" in url or "404" in url:
        raise ConnectionError(f"404 Not Found: {url}")  # deliberate failure path
    return {"content": f"Full page content from {url}. " * 20}


def summarize_text(text: str, max_points: int = 5) -> dict:
    return {"summary": [f"Key point {i + 1}" for i in range(min(max_points, 5))]}


def format_citation(title: str, url: str, accessed_date: str = None) -> dict:
    date = accessed_date or "2025-01-15"
    return {"citation": f'"{title}." Available at: {url}. Accessed: {date}.'}


def save_to_file(filename: str, content: str) -> dict:
    return {"status": "saved", "path": f"/output/{filename}", "bytes": len(content)}


# ── Dispatcher with per-tool error handling ──────────────────
tool_functions = {
    "web_search": web_search, "fetch_page": fetch_page,
    "summarize_text": summarize_text, "format_citation": format_citation,
    "save_to_file": save_to_file,
}


def execute_tool(name: str, inputs: dict) -> tuple[str, bool]:
    """Execute a tool, returning (result_json, is_error). Never raises."""
    func = tool_functions.get(name)
    if not func:
        return json.dumps({"error": f"Unknown tool: {name}"}), True
    try:
        result = func(**inputs)
        return json.dumps(result), False
    except Exception as e:
        return json.dumps({"error": str(e), "tool": name}), True


# ── ToolRegistry: filter the toolbox by phase ────────────────
class ToolRegistry:
    """Manages tools and filters them by context."""

    def __init__(self):
        self._tools: dict[str, dict] = {}
        self._tags: dict[str, set[str]] = {}

    def register(self, tool: dict, tags: list[str] = None):
        name = tool["function"]["name"]
        self._tools[name] = tool
        self._tags[name] = set(tags or [])

    def unregister(self, name: str):
        self._tools.pop(name, None)
        self._tags.pop(name, None)

    def get_tools_for_context(self, tags: list[str] = None, names: list[str] = None) -> list[dict]:
        if names:
            return [self._tools[n] for n in names if n in self._tools]
        if tags:
            tag_set = set(tags)
            return [self._tools[n] for n, t in self._tags.items() if t & tag_set]
        return list(self._tools.values())


def build_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(TOOLS[0], tags=["research", "search"])
    registry.register(TOOLS[1], tags=["research", "fetch"])
    registry.register(TOOLS[2], tags=["research", "analysis"])
    registry.register(TOOLS[3], tags=["citation"])
    registry.register(TOOLS[4], tags=["output"])
    return registry


if __name__ == "__main__":
    registry = build_registry()
    print("Tools, dispatcher, and registry ready.")
    print(f"  All tools:     {[t['function']['name'] for t in registry.get_tools_for_context()]}")
    print(f"  Research only: {[t['function']['name'] for t in registry.get_tools_for_context(tags=['research'])]}")
    print(f"  Dispatch test: {execute_tool('web_search', {'query': 'AI agents'})[0][:80]}...")
    print(f"  Error test:    {execute_tool('fetch_page', {'url': 'https://broken.example.com/404'})}")
