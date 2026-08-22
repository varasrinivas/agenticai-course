---
description: Validate a capstone project for accuracy, executability, and completeness
argument-hint: [CAPSTONE_ID DOMAIN e.g. CAPSTONE-3 DOMAIN-A, or CAPSTONE-3 for all domains, or CAPSTONE-8 for a standalone capstone]
---

Validate the capstone project $ARGUMENTS for technical accuracy and student executability.

Read `prompts/19-sdk-tier-policy.md` FIRST — it is the declared **source of truth** for which
tooling every capstone uses, and PASS 6 below is scored against it.
Read `prompts/03-capstone-domains.md` for the domain specifications.
Read `prompts/04-quality-standards.md` for content quality rules.
Read `prompts/07-depth-rules.md` for explanation quality rules (Rule 13 for lab steps, Rule 14 for
capstone packets).
Read `prompts/17-spec-driven-development.md` if the capstone is in the spec-driven set.

Find the capstone HTML file in `output/courses/claude-agents/` (glob match on the capstone ID and,
if given, the domain). Find the matching lab in `labs/capstone-<n>-<slug>/`.

**Capstone ID forms.** Domain capstones are `CAPSTONE-{1..5,7}-DOMAIN-{A|B|C}`. Standalone
capstones use a slug instead of a domain — currently `CAPSTONE-6-data-pipeline-testing`,
`CAPSTONE-8-oracle-to-postgres-migration`, `CAPSTONE-8B-skills-first-migration` and
`CAPSTONE-9-behavioral-health-modernization`. If the argument names a standalone capstone, do not
look for domain variants and skip the domain-letter checks in PASS 11.

Run ALL of the following validation passes:

## PASS 1: Prerequisites Check
- List every module referenced as a prerequisite
- For each prerequisite module, verify it exists in `output/courses/claude-agents/`
- Check: does the capstone use any concept NOT covered in a prerequisite module? If yes, flag it.
- Report: prerequisites satisfied / missing

## PASS 2: Environment Setup Validation
Check that the capstone provides COMPLETE setup instructions:
- [ ] Python version specified (e.g., "Python 3.10+")
- [ ] Node.js version specified (if applicable)
- [ ] ALL pip/npm packages listed with version numbers
- [ ] A single copy-pasteable install command. **The expected packages depend on the tier** (see
      PASS 6): Tier 1 installs `anthropic`; Tier 3 installs `claude-agent-sdk`. A Tier 3 capstone
      whose install command does not include `claude-agent-sdk` is a critical issue.
- [ ] Environment variable setup instructions (`ANTHROPIC_API_KEY` at minimum)
- [ ] Any external services needed (databases, APIs) are either mocked, containerized with the
      lab, or have free-tier setup instructions
- [ ] Operating system assumptions stated (Windows/Mac/Linux, any WSL requirements)
- [ ] If the lab ships containers: image sizes, first-boot time, and any architecture caveats
      (e.g. x86-only images under emulation on Apple Silicon) are stated up front, with a fallback
      path for students who cannot run them
- [ ] No package that requires a paid subscription without stating it
- Flag: any dependency mentioned in code but NOT in the setup instructions

## PASS 3: Code Completeness — Can a Student Copy-Paste and Run?
For EVERY code block presented as complete and runnable:
- [ ] Complete imports at the top (no missing imports)
- [ ] No placeholder comments like "# ... implement here" or "# rest of implementation"
- [ ] No undefined variables or functions referenced
- [ ] No hardcoded file paths that only work on the author's machine
- [ ] All API keys read from environment variables, never hardcoded
- [ ] Error handling present (try/except or try/catch)
- [ ] Expected output shown after the code block
- [ ] If code depends on a previous step's output, that dependency is explicit ("This uses the
      `chunks` variable from Step 1")
- Flag: any code block where a student pressing Ctrl+C → paste → Enter would get an error

**Exempt from the no-TODO rule:** code blocks explicitly presented as a `starter/` skeleton the
student is being asked to fill in. Those are supposed to contain numbered TODOs. The distinction
is whether the surrounding prose says "here is the code" or "here is what you build".

## PASS 4: Mock Data / Fixture Validation
- [ ] Data is provided with the lab — never "connect to your real database"
- [ ] Data ships either as inline files, creation scripts, or **seed scripts for a container the
      lab brings up itself**. A containerized fixture database counts as provided data; a
      connection string pointing at something the student has to supply does not.
- [ ] Data is realistic enough to demonstrate the concept (not just `{"test": "data"}`)
- [ ] Data matches the schema referenced in code (field names, types, nesting)
- [ ] If the lab plants deliberate defects for the student to find, they are documented in the
      lab's own notes and covered by a test, so a student never chases a bug that is actually a
      typo in the course material
- [ ] For UCC domain: realistic `filing_number`, `debtor_name`, `secured_party_name`,
      `state_code`, `collateral_description` fields
- [ ] For Healthcare domain: realistic CPT codes, ICD-10 codes, payer names
- [ ] For B2B domain: realistic PO numbers, SKUs, carrier tracking formats
- Flag: any mismatch between the data schema and the code that accesses it

## PASS 5: Step Sequence — Does the Order Work?
Walk through the capstone as a student would, step by step:
- [ ] Steps are numbered sequentially
- [ ] Each step's OUTPUT is the next step's INPUT (no gaps)
- [ ] No step requires running something that hasn't been created yet
- [ ] File creation order is correct (don't import a module before creating it)
- [ ] If there are multiple files, the creation order and directory structure are specified
- [ ] Each step has a "checkpoint" — how the student knows the step succeeded
- [ ] Expected terminal output or response shown for verification
- [ ] Each step has troubleshooting (2–3 anticipated errors with fixes), per depth Rule 13
- Flag: any step where a student following instructions exactly would get stuck

## PASS 6: SDK Tier Compliance — Does the Code Match the Tier Policy?

**Look up the capstone's tier in the Per-Module Tier Index of `prompts/19-sdk-tier-policy.md`
before checking anything else.** The correct API pattern is different for each tier, so a check
that is a pass at one tier is a critical failure at another. Do not apply a single "correct SDK
usage" standard across all capstones.

Current assignment: **CAPSTONE-1 through 5 and 7 are Tier 3** (all domains). **CAPSTONE-6 is
deliberately Tier 1** — the non-agent baseline. **CAPSTONE-8, CAPSTONE-8B and CAPSTONE-9 are Tier 3.** If a capstone is not in
the index, default to Tier 1 and raise a warning that the index needs updating.

### If Tier 1 (CAPSTONE-6, and any capstone the index marks Tier 1)
- [ ] Uses `anthropic.Anthropic()` and `client.messages.create()` directly
- [ ] Tool definitions are plain JSON dicts with `name`, `description`, `input_schema`
- [ ] The tool-use loop is a hand-written `while` loop checking `stop_reason`
- [ ] Does **NOT** import `claude_agent_sdk`
- Flag: a Tier 1 capstone that imports the Agent SDK. It is teaching the layer this tier exists
  to expose, and the contrast CAPSTONE-6 is built to demonstrate is lost.

### If Tier 3 (CAPSTONE-1..5, 7, 8, 8B, 9)
- [ ] The primary `solution/` imports from `claude_agent_sdk` — `query`, `tool`,
      `create_sdk_mcp_server`, `ClaudeAgentOptions`, `AssistantMessage`, `HookMatcher`,
      `PermissionResultAllow`, `PermissionResultDeny`
- [ ] Tools are `@tool`-decorated async functions returning
      `{"content": [{"type": "text", "text": json.dumps(result)}]}`
- [ ] Tools are exposed through `create_sdk_mcp_server`, not called directly
- [ ] `query(prompt=..., options=ClaudeAgentOptions(...))` is the entry point
- [ ] **CRITICAL: no `client.messages.create()` anywhere outside `appendix/manual-loop.py`.**
      That file is the sanctioned exception and must be labeled "under the hood — for
      understanding, not for production."
- [ ] Subagents declared as `.claude/agents/<name>.md` with frontmatter (`name`, `description`,
      `tools`, optional `model`) — where the capstone uses subagents
- [ ] Hooks declared in `.claude/settings.json`
- [ ] Slash commands in `.claude/commands/` — where applicable
- [ ] Skills in `.claude/skills/<name>/SKILL.md` — where the capstone uses them. Frontmatter
      `name` (matching the directory) and `description`; bundled `references/` and `scripts/`
      must exist if the body points at them. Flag domain knowledge duplicated across subagent
      prompts instead of living in one Skill
- [ ] **`spec/agent-spec.md` is present.** Mandatory for every Tier 3 capstone. Its absence is a
      critical issue, not a warning.
- [ ] The spec follows the 12-section template in `prompts/17-spec-driven-development.md` and ends
      with checkable acceptance criteria, not aspirations
- [ ] The HTML has a spec-driven section walking the student through
      read spec → `/generate-from-spec` → diff against `solution/` → iterate on the spec
- Flag: a Tier 3 capstone missing `spec/agent-spec.md`, or whose `solution/` does not import
  `claude_agent_sdk`.

### Never, at any tier
- [ ] The lab does **not** mock the SDK by reimplementing `query()` as a wrapper around
      `client.messages.create()`. If offline tests are needed, exercise `HookMatcher`,
      `can_use_tool`, and `PermissionResultAllow`/`Deny` directly — the canonical pattern is
      `labs/capstone-4-agent-team/domain-a-healthcare/sdk_tests/`.
- [ ] No invented APIs. Only the imports and call shapes in the tier policy's cheat sheet appear.
      `@agent.tool` is not a real decorator; the correct one is `@tool` from `claude_agent_sdk`.
- Flag: any API surface that does not appear in the cheat sheet.

## PASS 7: API Accuracy — Tier-Independent Format Checks
These apply regardless of tier, because they are about the wire format rather than the abstraction:
- [ ] Tool/function schemas use correct JSON Schema (`type`, `properties`, `required`)
- [ ] `tool_use` response handling matches the current API (check `stop_reason`, read the
      `tool_use` content block) — Tier 1 only, since the SDK handles this at Tier 3
- [ ] `tool_result` message format is correct (`role: "user"`, content with `type: "tool_result"`
      and the matching `tool_use_id`) — Tier 1 only
- [ ] MCP server code uses the current `@modelcontextprotocol/sdk` API (if a standalone MCP
      server is being written rather than `create_sdk_mcp_server`)
- [ ] Model IDs are current and correctly spelled
- [ ] No deprecated patterns (old tool-use XML format, legacy completion endpoint)
- Flag: any API call that would return an error against the current SDK

## PASS 8: Conceptual Accuracy
- [ ] Technical explanations are factually correct
- [ ] Architecture diagrams match the actual code implementation
- [ ] Claimed performance numbers are realistic (not "reduces hallucinations by 99%")
- [ ] Cost estimates state what they cover (input vs output tokens) and are in the right ballpark
- [ ] Best practices match Anthropic's official documentation
- [ ] Anti-patterns are correctly identified (matches cert exam anti-patterns where applicable)
- Flag: any claim that contradicts Anthropic's documentation or established best practices

## PASS 9: Quiz/Assessment Accuracy
- [ ] Every quiz question has exactly ONE correct answer
- [ ] The correct answer is actually correct (verify against the capstone content)
- [ ] Wrong answers are plausible but clearly wrong (not trick questions)
- [ ] Every wrong answer has its own explanation of WHY it is wrong — a shared
      "Not quite, try again" teaches nothing, and the interesting part of a distractor is why it
      is tempting
- [ ] Questions test understanding, not memorization of arbitrary details
- [ ] At least 1 question requires applying knowledge to a new scenario (not just recall)
- Flag: any question where the "correct" answer is debatable or a wrong answer could be argued

## PASS 10: Student Experience Flow
Read through the entire capstone imagining you are a student with ONLY the knowledge from
prerequisite modules:
- [ ] Is the difficulty progression smooth? (doesn't jump from easy to impossible)
- [ ] Are there enough "small wins" early to build confidence?
- [ ] If a student gets stuck, is there enough troubleshooting guidance?
- [ ] Common error messages are anticipated with solutions
- [ ] If the lab is designed to fail on the first run (a planted defect), the HTML says so
      explicitly at the point of failure, so the student debugs the exercise rather than their
      own setup
- [ ] Stretch goals are clearly marked as OPTIONAL
- [ ] The final "What You Built" section makes the student feel accomplished
- [ ] Time estimate is realistic (not "30 minutes" for something that takes 3 hours)
- Flag: any point where a student would likely get frustrated or lost

## PASS 11: Domain-Specific Validation

Skip this pass for standalone capstones with no domain letter (CAPSTONE-6, CAPSTONE-8, 8B, 9). Validate
those against their own brief in `prompts/modules/CAPSTONE-{N}*.md` instead.

For Healthcare Pre-Auth (Domain A):
- [ ] CPT and ICD-10 codes used are real and correctly formatted
- [ ] Clinical workflow makes medical sense (pre-auth → review → determination)
- [ ] HIPAA/PHI callouts present where patient data is handled
- [ ] No actual patient data — all mock data is clearly fictional

For B2B Ecommerce (Domain B):
- [ ] PO lifecycle stages are realistic (confirmed → in-production → shipped → delivered)
- [ ] Carrier tracking formats are plausible
- [ ] Pricing/contract logic makes business sense
- [ ] SLA calculations are correct

For UCC Data Engineering (Domain C):
- [ ] UCC filing types are correct (UCC-1, UCC-3 amendment/continuation/termination)
- [ ] State SOS data format descriptions are plausible
- [ ] Entity resolution logic makes sense
- [ ] Medallion Architecture layers (Bronze/Silver/Gold) are used correctly
- [ ] Lien risk scoring logic is reasonable

## FINAL REPORT

Generate a report with:
1. **Overall Status**: PASS / PASS WITH WARNINGS / NEEDS FIXES
2. **Tier**: which tier the index assigns this capstone, and whether the code complies
3. **Pass Summary**: X of 11 passes clean, Y with warnings, Z with failures
4. **Critical Issues** (must fix before publishing):
   - Code that won't run
   - Missing dependencies
   - Wrong API format for the capstone's tier
   - A Tier 3 capstone missing `spec/agent-spec.md`
   - A Tier 3 `solution/` that does not import `claude_agent_sdk`
   - A lab that mocks the SDK over `client.messages.create()`
   - Incorrect quiz answers
5. **Warnings** (should fix):
   - Missing checkpoints or troubleshooting
   - Thin explanations
   - Missing error handling
   - Quiz distractors without individual explanations
6. **Suggestions** (nice to have):
   - Better mock data
   - Additional troubleshooting tips
   - Extra stretch goals
7. **Estimated Fix Time**: how long to address all critical issues

If a finding turns on which tier applies, cite the row from the Per-Module Tier Index you used.
Where this command and `prompts/19-sdk-tier-policy.md` appear to disagree, **the tier policy
wins** — report the discrepancy as a bug in this command rather than as a defect in the capstone.

Ask: "Should I auto-fix the critical issues?"
