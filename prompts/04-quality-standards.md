# Content Quality Standards & Constraints

## Content Rules

1. Every technical term MUST be defined on first use (tooltip + inline explanation)
2. Every "why" must be answered before the "how"
3. Code examples must be COMPLETE and RUNNABLE (not pseudocode)
4. Error handling must be included in ALL code examples — no happy-path-only code
5. Security considerations called out with ⚠️ warning boxes
6. Cost implications noted with 💰 callouts where relevant
7. Every module must link back to at least one concept from a previous module
8. All API calls use Claude's current API format (Anthropic SDK v0.30+, Messages API)
9. Include version numbers for all dependencies
10. Never hardcode API keys — always use environment variables with clear instructions
11. **SDK tier compliance** — every module follows the tier assigned in `prompts/19-sdk-tier-policy.md`:
    - Tier 1 (M01–M11, M15, M18, M20, M21, M22, CAPSTONE-6): raw Messages API only, no `claude-agent-sdk` import
    - Tier 2 (M12, M13, M14, M16, M17, M19): ship BOTH `solution/` (raw) AND `solution-sdk/` (SDK), with side-by-side comparison
    - Tier 3 (M15B, M22B, M25–M27B, CAPSTONE-1..5, 7): primary `solution/` uses `claude-agent-sdk`; capstones + M15B also ship `spec/agent-spec.md`
12. **No fake SDK simulations** — never reimplement `query()` with `client.messages.create()` and call it "the SDK." If the lab needs to run offline, use `claude-agent-sdk`'s real testing primitives (see `labs/capstone-4-agent-team/domain-a-healthcare/sdk_tests/` for the canonical pattern)
13. **Subagents and hooks live in config files** — Tier 3 multi-agent labs declare subagents in `.claude/agents/<name>.md`; Tier 3 guardrail labs declare hooks in `.claude/settings.json`. Don't reinvent these as Python decorators when they belong in config.

## Accessibility Requirements

- All animations MUST have a `prefers-reduced-motion` media query fallback (show static diagram)
- All interactive elements MUST have proper ARIA labels
- All interactive elements MUST be keyboard navigable (Tab, Enter, Escape)
- All images/diagrams MUST have alt text
- Color is NEVER the only indicator of state (use icons + text alongside color)
- Minimum contrast ratio: 4.5:1 for body text, 3:1 for large text
- Focus indicators must be visible on all interactive elements

## Code Example Standards

- Both Python AND Node.js/TypeScript for every code example
- Use tabbed panels to switch between languages
- Every code block has a "Copy" button
- **For Tier 2/3 SDK code blocks**, use the imports and patterns from the cheat sheet in `prompts/19-sdk-tier-policy.md` verbatim — do not invent alternative SDK APIs
- **For Tier 2 modules**, the HTML must include a "Manual vs SDK — side by side" comparison section showing the same logic both ways
- Use syntax highlighting via Prism.js or highlight.js (loaded from CDN)
- Include complete import statements
- Include error handling (try/except or try/catch)
- Include inline comments explaining non-obvious logic
- Show expected output as a separate, clearly labeled block
- Use environment variables for API keys:
  ```python
  # Python
  import anthropic
  client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY env var
  ```
  ```javascript
  // Node.js
  import Anthropic from '@anthropic-ai/sdk';
  const client = new Anthropic(); // reads ANTHROPIC_API_KEY env var
  ```

## HTML File Constraints

- Every HTML file must be SELF-CONTAINED (all CSS/JS inline)
- External resources allowed ONLY: Google Fonts CDN, Prism.js/highlight.js CDN
- File size target: Under 150KB per module
- All `<a>` links to external sites: `target="_blank" rel="noopener noreferrer"`
- Semantic HTML: use `<section>`, `<article>`, `<nav>`, `<aside>`, `<figure>`, `<figcaption>`
- Every section heading (`<h2>`, `<h3>`) must have an `id` attribute for sidebar nav anchoring
- Include `<meta charset="UTF-8">` and `<meta name="viewport" content="width=device-width, initial-scale=1.0">`
- Page title format: `M{XX}: {Module Title} | Building AI Agents with Claude`

## Quiz Standards

- Minimum 5 questions per module
- Mix of question types:
  - Multiple choice (single correct answer)
  - Multiple select (2+ correct answers)
  - Code completion (fill in the blank in a code snippet)
  - Ordering/sequencing (drag steps into correct order)
- Every wrong answer has an explanation of WHY it's wrong
- Every correct answer has a reinforcing explanation
- No trick questions — test understanding, not gotcha trivia
- At least 1 question should reference a concept from a PREVIOUS module

## Navigation Requirements

- Sticky sidebar with clickable section headings
- "Previous Module" and "Next Module" links at top and bottom
- Smooth scroll to sections on sidebar click
- Progress indicator that updates as user scrolls through sections
- Mobile: collapsible sidebar or bottom navigation bar
