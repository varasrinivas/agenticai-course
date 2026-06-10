"""
Replaces prose/comment/annotation references to "Claude" with "the model"
in the open source track modules.

Pass 1: Replaces in HTML text nodes (outside tags)
Pass 2: Replaces inside <script> JS string literals (quiz answers, animation annotations)
Pass 3: Replaces inside code block *comments* (lines starting with # or //)

Protects:
- Actual code statements (not comments)
- href/src/id attribute values
- "View Claude version" link text (intentional)
- "claude-agent-sdk" package references in code (leave as-is, they're real package names)
- "Claude Certified" / "Claude Code" product names
"""
import re
import sys
from pathlib import Path

FOLDER = Path(__file__).parent.parent / "output" / "opensource"

# ─── Literal string swaps (done first, before regex) ────────────────────────
LITERAL_SWAPS = [
    # Course title
    ("Building AI Agents with Claude", "Building AI Agents with Open Source Models"),
    # Keep these — intentional references
    # "View Claude version" → we'll protect below
]

# Strings to protect (will be temporarily replaced with placeholders)
PROTECT_EXACT = [
    "View Claude version",
    "Claude Certified",
    "Claude Code",
    "claude-agent-sdk",
    "ClaudeAgentOptions",
    "claude_agent_sdk",
    "docs.anthropic.com",
    "claude-agent-course",
]


def protect_exact(content):
    protected = {}
    for i, s in enumerate(PROTECT_EXACT):
        placeholder = f"__PROTECT_{i}__"
        protected[placeholder] = s
        content = content.replace(s, placeholder)
    return content, protected


def restore_exact(content, protected):
    for placeholder, original in protected.items():
        content = content.replace(placeholder, original)
    return content


# ─── HTML attribute protection ───────────────────────────────────────────────
def protect_attributes(content):
    """Protect non-descriptive HTML attributes. Intentionally excludes aria-label
    and title so their text gets the same Claude→model treatment as prose."""
    attrs = []

    def save(m):
        attrs.append(m.group(0))
        return f"__ATTR_{len(attrs)-1}__"

    # Do NOT include aria-label or title — they are descriptive text, not code paths
    content = re.sub(
        r'(?:href|src|id|class|data-[\w-]+|name|value|placeholder|for|action|method|type)\s*=\s*"[^"]*"',
        save, content
    )
    content = re.sub(
        r"(?:href|src|id|class|data-[\w-]+|name|value|placeholder|for|action|method|type)\s*=\s*'[^']*'",
        save, content
    )
    return content, attrs


def restore_attributes(content, attrs):
    for i, attr in enumerate(attrs):
        content = content.replace(f"__ATTR_{i}__", attr)
    return content


# ─── Code block handling (protect code, but update comments inside) ──────────
def process_code_block_comments(block_text):
    """Within a code block, replace Claude in:
    - Comment lines (# ... or // ...)
    - String display labels like print(f"Claude: ...") or console.log(`Claude: ...`)
    - Docstrings (triple-quoted strings)
    """
    lines = block_text.split("\n")
    result = []
    for line in lines:
        stripped = line.lstrip()
        is_comment = (
            stripped.startswith("# ")
            or stripped.startswith("// ")
            or stripped.startswith("<!-- ")
            or stripped.startswith("* ")
            or stripped == "#"
            or stripped == "//"
        )
        # Display label in print/console that shows model name
        is_display_label = bool(re.search(
            r'print\s*\(\s*[f"\'].*Claude[:\s]|console\.\w+\s*\(\s*[`"\'].*Claude[:\s]'
            r'|""".*Claude.*"""|\'\'\'.*Claude.*\'\'\'',
            line
        ))
        # Docstring lines
        is_docstring = stripped.startswith('"""') or stripped.startswith("'''")

        if is_comment or is_display_label or is_docstring:
            line = replace_claude_word(line)
        result.append(line)
    return "\n".join(result)


def protect_code_blocks(content):
    """Protect code blocks but update comments inside them."""
    blocks = []

    def save_pre(m):
        processed = process_code_block_comments(m.group(0))
        blocks.append(processed)
        return f"__CODEBLOCK_{len(blocks)-1}__"

    def save_code(m):
        processed = process_code_block_comments(m.group(0))
        blocks.append(processed)
        return f"__CODEBLOCK_{len(blocks)-1}__"

    content = re.sub(r"<pre[^>]*>.*?</pre>", save_pre, content, flags=re.DOTALL)
    content = re.sub(r"<code[^>]*>.*?</code>", save_code, content, flags=re.DOTALL)
    return content, blocks


def restore_code_blocks(content, blocks):
    for i, block in enumerate(blocks):
        content = content.replace(f"__CODEBLOCK_{i}__", block)
    return content


# ─── Script tag handling (replace Claude in string literals) ─────────────────
def process_script_strings(script_text):
    """Replace Claude in JS/Python string literals within script tags."""
    # Match single-quoted strings: '...'
    def replace_in_single_quoted(m):
        s = m.group(0)
        return replace_claude_word(s)

    # Match double-quoted strings: "..."  (but not in code paths)
    def replace_in_double_quoted(m):
        s = m.group(0)
        # Don't modify strings that look like file paths, imports, or model names
        if re.search(r'\.html|\.js|\.py|\.mjs|import |require\(|anthropic|openai', s):
            return s
        return replace_claude_word(s)

    # Replace Claude in single-quoted JS strings
    script_text = re.sub(r"'[^'\\]*(?:\\.[^'\\]*)*'", replace_in_single_quoted, script_text, flags=re.DOTALL)
    # Replace Claude in double-quoted JS strings (carefully)
    script_text = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', replace_in_double_quoted, script_text, flags=re.DOTALL)
    return script_text


def protect_scripts(content):
    scripts = []

    def save(m):
        processed = process_script_strings(m.group(0))
        scripts.append(processed)
        return f"__SCRIPT_{len(scripts)-1}__"

    content = re.sub(r"<script[^>]*>.*?</script>", save, content, flags=re.DOTALL)
    return content, scripts


def restore_scripts(content, scripts):
    for i, script in enumerate(scripts):
        content = content.replace(f"__SCRIPT_{i}__", script)
    return content


# ─── Core Claude → "the model" replacements ─────────────────────────────────
def replace_claude_word(text):
    """Replace 'Claude' with 'the model' or 'The model' based on position."""
    # Claude's → the model's
    text = re.sub(r"\bClaude's\b", "the model's", text)
    text = re.sub(r"\bClaude's\b", "the model's", text)  # smart apostrophe

    # After sentence-ending punctuation + space → capitalize
    text = re.sub(r"(?<=[.!?] )Claude\b", "The model", text)
    # After > tag → capitalize
    text = re.sub(r"(?<=>)Claude\b", "The model", text)
    # After newline or at line start → capitalize
    text = re.sub(r"(?:^|\n)([ \t]*)Claude\b", lambda m: m.group(0).replace("Claude", "The model"), text)

    # All remaining standalone Claude → the model (lowercase, mid-sentence)
    text = re.sub(r"\bClaude\b", "the model", text)
    return text


def fix_grammar(content):
    """Fix awkward grammar created by replacements."""
    # "a the model" → "the model"
    content = re.sub(r"\ba the model\b", "the model", content, flags=re.IGNORECASE)
    content = re.sub(r"\ban the model\b", "the model", content, flags=re.IGNORECASE)
    # "the the model" → "the model"
    content = re.sub(r"\bthe the model\b", "the model", content, flags=re.IGNORECASE)
    # "The The model" → "The model"
    content = re.sub(r"\bThe The model\b", "The model", content)
    # "model model" (double replacement artifact)
    content = re.sub(r"\bthe model the model\b", "the model", content, flags=re.IGNORECASE)
    return content


# ─── Main processing ─────────────────────────────────────────────────────────
def process_file(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    original_count = len(re.findall(r"\bClaude\b", content))

    # Step 1: Literal swaps (course title etc.)
    for original, replacement in LITERAL_SWAPS:
        content = content.replace(original, replacement)

    # Step 2: Protect exact strings that must never change
    content, protected = protect_exact(content)

    # Step 3: Protect and process code blocks (comments updated inside)
    content, code_blocks = protect_code_blocks(content)

    # Step 4: Protect and process <script> tags (strings updated inside)
    content, scripts = protect_scripts(content)

    # Step 5: Protect HTML attribute values
    content, attrs = protect_attributes(content)

    # Step 6: Replace Claude in remaining prose HTML
    content = replace_claude_word(content)

    # Step 7: Fix grammar artifacts
    content = fix_grammar(content)

    # Step 8: Restore everything
    content = restore_attributes(content, attrs)
    content = restore_scripts(content, scripts)
    content = restore_code_blocks(content, code_blocks)
    content = restore_exact(content, protected)

    final_count = len(re.findall(r"\bClaude\b", content))

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

    return original_count, final_count


def main():
    files = sorted(FOLDER.glob("M*.html"))
    print(f"Processing {len(files)} files\n")
    total_before = 0
    total_after = 0
    for path in files:
        before, after = process_file(path)
        total_before += before
        total_after += after
        status = "OK  " if after <= 5 else ("WARN" if after <= 15 else "FAIL")
        print(f"[{status}]  {path.name:<54}  {before:>4} -> {after:>3} remaining")
    print(f"\nTotal: {total_before} -> {total_after} remaining")


if __name__ == "__main__":
    main()
