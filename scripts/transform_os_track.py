"""
Transform course modules to Open Source (Ollama/Mistral) track.
"""
import re
import os

BASE = "D:/work/ai-workspace/tutorials/repo/claude-agent-course-final-adv"


def transform(content, source_slug, track_pos, prev_slug, next_slug, prev_label, next_label):
    """Apply all OS track transformations to the HTML content."""

    # ── Python imports ─────────────────────────────────────────────────────────
    content = content.replace("import anthropic\n", "from openai import OpenAI\n")
    content = content.replace("import anthropic\r\n", "from openai import OpenAI\r\n")
    content = content.replace("from anthropic import Anthropic", "from openai import OpenAI")
    content = content.replace("import Anthropic from '@anthropic-ai/sdk'", "import OpenAI from 'openai'")
    content = content.replace('import Anthropic from "@anthropic-ai/sdk"', 'import OpenAI from "openai"')
    content = content.replace("import Anthropic from &apos;@anthropic-ai/sdk&apos;", "import OpenAI from &apos;openai&apos;")

    # ── Python client ──────────────────────────────────────────────────────────
    content = content.replace(
        "anthropic.Anthropic()",
        'OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")',
    )
    # Standalone Anthropic() (no qualifier)
    content = re.sub(
        r"(?<!\w)Anthropic\(\)",
        'OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")',
        content,
    )

    # ── TypeScript client ──────────────────────────────────────────────────────
    content = re.sub(
        r"new Anthropic\(\)",
        "new OpenAI({ baseURL: 'http://localhost:11434/v1', apiKey: 'ollama' })",
        content,
    )
    # TS type annotations
    content = content.replace("Anthropic.Tool[]", "object[]")
    content = content.replace("Anthropic.MessageParam[]", "object[]")
    content = content.replace("Anthropic.TextBlock", "object")
    content = content.replace("Anthropic.ToolResultBlockParam[]", "object[]")
    content = content.replace("Anthropic.ToolResultBlockParam", "object")
    content = re.sub(r": Anthropic\.\w+", "", content)
    content = re.sub(r" as Anthropic\.\w+", "", content)

    # ── messages.create → chat.completions.create ──────────────────────────────
    content = content.replace("client.messages.create(", "client.chat.completions.create(")
    content = content.replace("claude.messages.create(", "claude.chat.completions.create(")
    content = content.replace("client.messages.create({", "client.chat.completions.create({")

    # ── Model strings ──────────────────────────────────────────────────────────
    for model in [
        "claude-sonnet-4-6",
        "claude-opus-4-7",
        "claude-opus-4-8",
        "claude-haiku-4-5-20251001",
        "claude-haiku-4-5",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    ]:
        content = content.replace(f'"{model}"', '"mistral"')
        content = content.replace(f"'{model}'", "'mistral'")

    # ── Remove standalone max_tokens lines ────────────────────────────────────
    content = re.sub(r"\n([ \t]+)max_tokens=\d+,?\n", "\n", content)
    content = re.sub(r"\n([ \t]+)max_tokens: \d+,?\n", "\n", content)

    # ── system= kwarg → remove (OpenAI schema uses messages list) ─────────────
    # Single-line Python
    content = re.sub(r"\n[ \t]+system=['\"][^'\"]*['\"],?\n", "\n", content)
    # Single-line TS
    content = re.sub(r"\n[ \t]+system: ['\"][^'\"]*['\"],?\n", "\n", content)
    # Keyword ref
    content = re.sub(r"\n[ \t]+system=SYSTEM_PROMPT,?\n", "\n", content)
    content = re.sub(r"\n[ \t]+system: SYSTEM_PROMPT,?\n", "\n", content)
    content = re.sub(r"\n[ \t]+system=CLASSIFY_PROMPT,?\n", "\n", content)
    content = re.sub(r"\n[ \t]+system: CLASSIFY_PROMPT,?\n", "\n", content)
    content = re.sub(r"\n[ \t]+system=DECOMPOSE_PROMPT,?\n", "\n", content)
    # Multi-line string  system=(  "..."  ),
    content = re.sub(
        r"\n[ \t]+system=\(\n(?:[ \t]+['\"][^'\"]*['\"],?\n)+[ \t]+\),",
        "",
        content,
    )
    # system=(  "line1"  "line2"  ) across lines with no comma needed
    content = re.sub(
        r"\n[ \t]+system=\(\n(?:[ \t]+\"[^\"]*\"\n)+[ \t]+\),?",
        "",
        content,
    )

    # ── response content access ────────────────────────────────────────────────
    content = content.replace("response.content[0].text", "response.choices[0].message.content")
    content = content.replace("resp.content[0].text", "resp.choices[0].message.content")
    # remaining .content[0].text
    content = content.replace(".content[0].text", ".choices[0].message.content")
    # TS patterns
    content = re.sub(
        r"response\.content\.find\([^)]+\)\??\.text",
        "response.choices[0].message.content",
        content,
    )
    content = content.replace("textBlock?.text", "response.choices[0].message.content")

    # ── stop_reason / finish_reason (only in code blocks) ─────────────────────
    content = content.replace('response.stop_reason == "end_turn"', 'response.choices[0].finish_reason == "stop"')
    content = content.replace("response.stop_reason == 'end_turn'", "response.choices[0].finish_reason == 'stop'")
    content = content.replace('resp.stop_reason == "end_turn"', 'resp.choices[0].finish_reason == "stop"')
    content = content.replace('response.stop_reason === "end_turn"', 'response.choices[0].finish_reason === "stop"')
    content = content.replace('resp.stop_reason === "end_turn"', 'resp.choices[0].finish_reason === "stop"')
    content = re.sub(r"stop_reason: \{response\.stop_reason\}", "finish_reason: {response.choices[0].finish_reason}", content)
    content = re.sub(r"\(stop_reason: \{response\.stop_reason\}\)", "(finish_reason: {response.choices[0].finish_reason})", content)

    # ── Tool definitions: input_schema → parameters ───────────────────────────
    content = content.replace('"input_schema":', '"parameters":')
    content = content.replace("'input_schema':", "'parameters':")
    content = content.replace("input_schema:", "parameters:")

    # ── tool_use block type check → tool_calls ────────────────────────────────
    content = content.replace('block.type == "tool_use"', 'block.type == "function"')
    content = content.replace("block.type == 'tool_use'", "block.type == 'function'")
    content = content.replace('b.type == "tool_use"', 'b.type == "function"')
    content = content.replace('block.type === "tool_use"', 'block.type === "function"')
    content = content.replace('b.type === "tool_use"', 'b.type === "function"')
    content = content.replace('stop_reason == "tool_use"', 'finish_reason == "tool_calls"')
    content = content.replace("stop_reason == 'tool_use'", "finish_reason == 'tool_calls'")
    content = content.replace('stop_reason === "tool_use"', 'finish_reason === "tool_calls"')

    # ── Tool result format ────────────────────────────────────────────────────
    content = content.replace('"type": "tool_result"', '"role": "tool"')
    content = content.replace("type: 'tool_result'", "role: 'tool'")
    content = content.replace('type: "tool_result"', 'role: "tool"')
    content = content.replace('"tool_use_id": block.id', '"tool_call_id": block.id')
    content = content.replace("tool_use_id: block.id", "tool_call_id: block.id")
    content = content.replace("tool_use_id: b.id", "tool_call_id: b.id")

    # ── import anthropic, base64 → split imports ─────────────────────────────
    content = re.sub(
        r"import anthropic, base64",
        "from openai import OpenAI\nimport base64",
        content,
    )

    # ── anthropic.APIError → openai.OpenAIError ───────────────────────────────
    content = content.replace("anthropic.APIError", "openai.OpenAIError")
    # Any remaining bare 'anthropic.' prefix in code (not in prose text)
    content = re.sub(r"\banthropicai\b", "openai", content)  # safety

    # ── TypeScript: new OpenAI(base_url=...) → new OpenAI({ baseURL: ... }) ──
    # Catches cases where Python-style kwargs leaked into TS (after chain of replacements)
    content = re.sub(
        r'new OpenAI\(base_url="http://localhost:11434/v1", api_key="ollama"\)',
        "new OpenAI({ baseURL: 'http://localhost:11434/v1', apiKey: 'ollama' })",
        content,
    )

    # ── pip/npm install ────────────────────────────────────────────────────────
    content = content.replace("pip install anthropic", "pip install openai")
    # pip install chromadb>=... anthropic>=...  →  pip install chromadb>=... openai
    content = re.sub(r'(pip install [^"\n<]*?)anthropic>=[\d.]+', r'\1openai', content)
    content = re.sub(r'pip install ["\']?anthropic>=[\d.]+["\']?', "pip install openai", content)
    content = re.sub(r"pip install ['\"]anthropic['\"]", "pip install openai", content)
    # npm install chromadb@... @anthropic-ai/sdk@...  →  ...openai
    content = re.sub(r'(// npm install [^\n<]*?)@anthropic-ai/sdk@[\d.^]+', r'\1openai', content)
    content = content.replace("npm install @anthropic-ai/sdk", "npm install openai")
    # Remaining @anthropic-ai/sdk references in comments
    content = re.sub(r'@anthropic-ai/sdk@?[\d.^]*', 'openai', content)
    # pip install "anthropic>=X.Y.Z" in HTML (HTML-encoded quotes)
    content = re.sub(r'pip install &quot;anthropic&gt;=[\d.]+&quot;', 'pip install openai', content)
    content = re.sub(r"pip install &apos;anthropic&gt;=[\d.]+&apos;", "pip install openai", content)
    # Raw text in prose: `pip install "anthropic>=0.30.0"` style (unencoded)
    content = re.sub(r'pip install "anthropic&gt;=[\d.]+"', 'pip install openai', content)
    content = re.sub(r'pip install `anthropic&gt;=[\d.]+`', 'pip install openai', content)
    # Module-not-found error message in prose about anthropic module
    content = re.sub(
        r"ModuleNotFoundError: No module named &apos;anthropic&apos;.*?pip install &quot;anthropic&gt;=[\d.]+&quot;",
        "ModuleNotFoundError: No module named 'openai' → Run pip install openai",
        content,
        flags=re.DOTALL,
    )

    # ── Progress indicator ────────────────────────────────────────────────────
    content = re.sub(r"Module \d+ of 30", f"OS Track · Module {track_pos} of 12", content)
    content = re.sub(r"<span>Module \d+ of 30</span>", f"<span>OS Track · Module {track_pos} of 12</span>", content)
    content = re.sub(
        r"Module \d+ of 30 &middot;",
        f"OS Track · Module {track_pos} of 12 &middot;",
        content,
    )
    content = re.sub(
        r"Module \d+ of 30 ·",
        f"OS Track · Module {track_pos} of 12 ·",
        content,
    )
    # Inline header-meta
    content = re.sub(
        r"Module 12 of 30 · 60",
        f"OS Track · Module {track_pos} of 12 · 60",
        content,
    )
    content = re.sub(
        r"Module 14 of 30</span>",
        f"OS Track · Module {track_pos} of 12</span>",
        content,
    )
    content = re.sub(
        r"Module 10 of 30</span>",
        f"OS Track · Module {track_pos} of 12</span>",
        content,
    )

    # ── Navigation links ──────────────────────────────────────────────────────
    # Replace prev/next hrefs throughout, but KEEP home (index.html) links
    content = re.sub(
        r'href="M\d+-[^"]+\.html"',
        lambda m: _update_href(m.group(0), prev_slug, next_slug),
        content,
    )

    # Update nav link text for next
    if next_label:
        content = re.sub(
            r"M\d+: [^<&]+(&rarr;|→)",
            f"{next_label} →",
            content,
        )
    if prev_label:
        content = re.sub(
            r"(←|&larr;) M\d+: [^<]+",
            f"← {prev_label}",
            content,
        )

    # Fix aria-label for nav links
    content = re.sub(
        r'aria-label="Next module: [^"]+"',
        f'aria-label="Next module: {next_label}"',
        content,
    )
    content = re.sub(
        r'aria-label="Previous module: [^"]+"',
        f'aria-label="Previous module: {prev_label}"',
        content,
    )

    # ── OS Track banner ───────────────────────────────────────────────────────
    banner = (
        '\n      <div style="background:rgba(249,115,22,0.1);border:1px solid #F97316;border-radius:12px;'
        'padding:1rem 1.5rem;margin-bottom:2rem;display:flex;align-items:flex-start;gap:1rem;">\n'
        '        <span style="font-size:1.5rem;flex-shrink:0">&#x1F999;</span>\n'
        "        <div>\n"
        "          <strong style=\"color:#F97316;font-family:'Bricolage Grotesque',sans-serif;display:block;margin-bottom:0.25rem\">Open Source Track &mdash; Mistral/Ollama Version</strong>\n"
        "          <span style=\"font-size:0.9rem;color:#94A3B8;\">All code examples use the <code style=\"font-family:'JetBrains Mono',monospace;background:#1A2740;padding:0.1rem 0.4rem;border-radius:4px\">openai</code> SDK pointing at a local Ollama server. "
        f'<a href="../{source_slug}" style="color:#D4A843;">View Claude version &rarr;</a> &middot; '
        '<a href="index.html" style="color:#D4A843;">OS Track Index &rarr;</a></span>\n'
        "        </div>\n"
        "      </div>"
    )

    # Insert after <main class="content"> opening tag
    content = re.sub(
        r'(<main[^>]*class="content"[^>]*>)',
        r"\1" + banner,
        content,
        count=1,
    )

    return content


def _update_href(href_str, prev_slug, next_slug):
    """Map old hrefs to new OS track relative hrefs."""
    # Extract the filename
    m = re.search(r'"([^"]+\.html)"', href_str)
    if not m:
        return href_str
    fname = m.group(1)

    # prev/next mapping
    if prev_slug and fname in _prev_srcs:
        return f'href="{prev_slug}"'
    if next_slug and fname in _next_srcs:
        return f'href="{next_slug}"'
    return href_str


# We'll set these globals per file
_prev_srcs = set()
_next_srcs = set()


def process_file(src_path, dst_path, source_slug, track_pos,
                 prev_slug, next_slug, prev_label, next_label,
                 prev_source_slugs, next_source_slugs):
    global _prev_srcs, _next_srcs
    _prev_srcs = prev_source_slugs
    _next_srcs = next_source_slugs

    with open(src_path, "r", encoding="utf-8") as f:
        content = f.read()

    content = transform(
        content, source_slug, track_pos,
        prev_slug, next_slug, prev_label, next_label,
    )

    with open(dst_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Written {dst_path} ({len(content):,} chars)")


out = os.path.join(BASE, "output")
os_out = os.path.join(BASE, "output", "opensource")

# ─── M09 ──────────────────────────────────────────────────────────────────────
process_file(
    src_path=os.path.join(out, "M09-rag-retrieval-augmented-generation.html"),
    dst_path=os.path.join(os_out, "M09-rag-retrieval-augmented-generation.html"),
    source_slug="M09-rag-retrieval-augmented-generation.html",
    track_pos="7",
    prev_slug="M08-conversation-management.html",
    next_slug="M12-react-agent-loop.html",
    prev_label="M08: Conversation Management",
    next_label="M12: ReAct Agent Loop",
    prev_source_slugs={"M08-conversation-management.html"},
    next_source_slugs={"M10-advanced-rag-patterns.html", "M10-advanced-rag-patterns-v1.html"},
)

# ─── M12 ──────────────────────────────────────────────────────────────────────
process_file(
    src_path=os.path.join(out, "M12-react-agent-loop.html"),
    dst_path=os.path.join(os_out, "M12-react-agent-loop.html"),
    source_slug="M12-react-agent-loop.html",
    track_pos="8",
    prev_slug="M09-rag-retrieval-augmented-generation.html",
    next_slug="M13-planning-task-decomposition.html",
    prev_label="M09: RAG",
    next_label="M13: Planning & Task Decomposition",
    prev_source_slugs={"M11-multi-layer-memory.html"},
    next_source_slugs={"M13-planning-task-decomposition.html"},
)

# ─── M13 ──────────────────────────────────────────────────────────────────────
process_file(
    src_path=os.path.join(out, "M13-planning-task-decomposition.html"),
    dst_path=os.path.join(os_out, "M13-planning-task-decomposition.html"),
    source_slug="M13-planning-task-decomposition.html",
    track_pos="9",
    prev_slug="M12-react-agent-loop.html",
    next_slug="M14-multi-agent-systems.html",
    prev_label="M12: ReAct Agent Loop",
    next_label="M14: Multi-Agent Systems",
    prev_source_slugs={"M12-react-agent-loop.html"},
    next_source_slugs={"M14-multi-agent-systems.html"},
)

print("All done.")
