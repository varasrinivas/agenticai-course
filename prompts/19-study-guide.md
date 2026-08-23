# Study Guide Specification

Generate a condensed study guide from the mobile course content. This is a single-page reference document students can print, save as PDF, or keep on their phone for quick review.

## What the Study Guide Contains

For EACH of the 30 modules, extract from the mobile HTML:
1. **Module title** and track
2. **The Big Idea** — one sentence core concept
3. **Key Pseudocode** — the essential pattern (5-8 lines max)
4. **Remember** — the most common misconception and correction

## Format

### output/study-guide.pdf — Print-ready PDF
- Dark theme with course branding (Bricolage Grotesque headings, Source Sans 3 body, JetBrains Mono for pseudocode)
- Generated using reportlab (Python)
- Cover page with course title, version, date
- Table of contents with page numbers
- One module per page (or half-page for short modules)
- Quick Reference Cards on the last 2-3 pages
- Footer: page number, track name, module number
- A4 and Letter size variants

### output/study-guide.html — Interactive web version
- Dark theme matching the course
- Accordion sections (click module title to expand)
- Search/filter by track
- Print-friendly CSS (@media print)
- Fits on phone screen

### output/study-guide.md — Markdown version
- Plain text, works everywhere
- Copy into Notion, Obsidian, Google Docs
- Git-friendly

## Structure

```
STUDY GUIDE: Building AI Agents with Claude
============================================

TRACK 0: OVERVIEW
─────────────────
M00: Agent Lifecycle
  Core: An agent is an LLM that uses tools, makes decisions, and loops
        until the task is done.
  Pattern:
    WHILE claude wants to use a tool:
      SEND question to claude
      IF tool_use: RUN tool, SEND result back
      ELSE: RETURN answer
  Watch out: Agents are NOT autonomous — they run YOUR code loop.

TRACK 1: FOUNDATIONS
────────────────────
M01: LLM Mental Model
  Core: LLMs predict the next token based on probability, not understanding.
  Pattern:
    input tokens → transformer → probability distribution → next token
  Watch out: LLMs don't "understand" — they predict likely continuations.

M02: Tokens
  Core: Tokens are the units LLMs read — roughly 4 characters per token.
  Pattern:
    cost = (input_tokens × input_price) + (output_tokens × output_price)
  Watch out: Tokens are NOT words — "unhappiness" might be 3 tokens.

...continue for all 30 modules...

TRACK 9: CERT PREP
───────────────────
M27: Cert Exam Prep
  Core: 5 domains, 18 anti-patterns, 30 questions across 3 mock exams.
  Pattern:
    FOR each question:
      Identify the anti-pattern → name the correct pattern → explain why
  Watch out: Anti-patterns look correct at first glance. Read twice.

============================================
QUICK REFERENCE CARDS
============================================

THE TOOL USE LOOP (use everywhere):
  messages = [user question]
  WHILE true:
    response = claude(messages, tools)
    IF stop_reason == end_turn: RETURN response
    FOR each tool_use in response:
      result = EXECUTE tool
      APPEND tool_result to messages

THE 8 DESIGN PATTERNS:
  1. Single-Turn     — one tool, one call
  2. ReAct            — think → act → observe → loop
  3. Plan-Execute     — decompose first, then run
  4. Router           — classify input, route to handler
  5. Parallel Fan-Out — same task × many inputs
  6. Pipeline         — sequential stages
  7. Supervisor       — coordinator + specialist workers
  8. Autonomous+HITL  — agent runs, human approves key decisions

THE 3 AGENT APPROACHES:
  Raw (M15B):  250 lines, full control, write every line
  SDK (M26):    40 lines, hooks + sessions, SDK runs the loop
  Spec (M25): 100 lines of spec, Claude Code generates everything

COST CHEAT SHEET:
  Haiku:  $0.25/1M input, $1.25/1M output  — simple tasks
  Sonnet: $3/1M input, $15/1M output        — most agent work
  Opus:   $15/1M input, $75/1M output       — complex reasoning
  Prompt caching: 90% savings on repeated system prompts
  Batch API: 50% discount for non-real-time

THE 3 DEPLOYMENT TIERS:
  Tier 1: Docker + DuckDB (free, local, no cloud needed)
  Tier 2: GCP Cloud Run + BigQuery (pay-per-use, auto-scale)
  Tier 3: AWS Lambda + API Gateway (serverless, event-driven)
```

## Generation Command

> **Implemented.** `scripts/build-study-guide.py` builds the PDF (A4 + Letter)
> from `output/mobile/*.html`. Run `--check` first to see extraction coverage.
> The Quick Reference Cards below are **superseded** by
> `scripts/study-guide-quickref.md`, which is what the script reads — the cost
> figures in this file are prior-generation prices and should not be copied
> forward. The HTML and Markdown variants are still unbuilt.


Read all mobile HTML files from output/mobile/. For each module extract: the Big Idea card content, the Pseudocode card content, one misconception from the Misconceptions card. Compile into the study guide format above. Generate three files:

1. output/study-guide.pdf — Use reportlab to create a professional PDF with cover page, table of contents, one module per page, quick reference cards at the end. Use dark background (#0A1628) with light text (#E8ECF1) and gold accents (#D4A843). JetBrains Mono for pseudocode blocks.

2. output/study-guide.html — Interactive dark theme with accordion and search and print CSS.

3. output/study-guide.md — Plain markdown.

Include the Quick Reference Cards section at the end of all three formats covering the tool use loop and design patterns and approaches and cost sheet and deployment tiers.

## When to Generate

Generate AFTER mobile versions exist. The study guide reads FROM mobile content.

```
Order:
1. Fix all desktop modules (fix scripts)
2. Generate mobile (build-course.ps1 -Phase mobile)
3. Generate study guide (this command)
```
