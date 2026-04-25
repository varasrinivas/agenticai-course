# CLAUDE.md — Claude Agent Development Course

## Project Identity
This project generates the course "Building AI Agents with Claude: From Hello World to Autonomous Production Systems" — a 30-module, 9-track, beginner-friendly technical course with 5 domain-anchored capstone projects and a certification prep track for the Claude Certified Architect exam. Each module is a self-contained interactive HTML file with embedded CSS animations, code walkthroughs, quizzes, and visual explainers.

**M00 is the gateway module** — a code-free overview showing a working agent end-to-end, the agent architecture building blocks, the agent lifecycle (design → build → protect → observe → deploy), and how the course maps to each stage. Every learner starts here before M01.

**M15B and M22B are BUILD modules** — hands-on labs where the student builds a complete agent + subagent system (M15B) and deploys it to Local Docker, GCP Cloud Run, and AWS Lambda (M22B). These are 80% lab, 20% concept.

## Output Format
- Every module = ONE self-contained .html file in `output/`
- All CSS and JS MUST be inline (no external files in production output)
- During development, reference `shared/` files for reusable components
- The `build.js` script inlines shared components into final HTML
- Target file size: 80-150KB per module (optimize animations, no heavy assets)
- Import only: Google Fonts, Prism.js (syntax highlighting), and highlight.js from CDN

## File Conventions
- Module files: `output/M{XX}-{slug}.html` (e.g., `output/M09-rag-retrieval-augmented-generation.html`)
- Capstone files: `output/CAPSTONE-{N}-DOMAIN-{A|B|C}.html`
- Prompt files: `prompts/` — read these BEFORE generating any content
- Shared components: `shared/` — reusable CSS/JS to be inlined during build

## Key Design Rules (always apply)
1. Every technical term gets a tooltip definition on FIRST use
2. Every concept gets: analogy → technical definition → animated visual → "why it matters"
3. Code examples must be COMPLETE and RUNNABLE — never pseudocode
4. Both Python AND Node.js/TypeScript for every code example
5. Error handling in ALL code examples — no happy-path-only code
6. Accessibility: `prefers-reduced-motion` media query, ARIA labels, keyboard nav
7. All API calls use current Anthropic SDK format (Messages API, tool use — NOT legacy XML)
8. Interactive quiz (5 questions minimum) at end of every module
9. Progress indicator showing module position in the 30-module curriculum (M00-M27 + M15B + M22B)
10. Responsive layout — must work on tablet (768px) and desktop (1440px)
11. DEPTH RULES (read `prompts/07-depth-rules.md` before generating ANY content):
    - Analogies: minimum 3 sentences (BEFORE → PAIN → MAPPING)
    - Tech definitions: teach with plain English, define every sub-term
    - Code blocks: annotate in 3-5 chunks with WHAT/WHY/GOTCHA before each chunk
    - "Why It Matters": use concrete numbers and real scenarios, never abstract
    - Add conceptual bridges between major sections
    - Add "What Just Happened?" checkpoints after code blocks

## Domain Anchors (for capstone projects)
Three industry domains are used across all capstones. Read `prompts/03-capstone-domains.md` for full specifications:
- **Domain A**: Healthcare Pre-Authorization (clinical criteria, CPT/ICD codes, HIPAA)
- **Domain B**: B2B Ecommerce Order Tracking (PO lifecycle, carrier APIs, SLA management)
- **Domain C**: Public Records / UCC Data Engineering (lien risk, entity resolution, Medallion Architecture)

## Certification Integration
The course prepares learners for the **Claude Certified Architect – Foundations** exam (5 domains, 720/1000 passing score).
- Track 9 (M25-M27) covers cert-specific content: Claude Code config, hooks/sessions/Agent SDK, anti-patterns + exam practice
- Modules M03-M18 include "🎓 Cert Tip" callout boxes — see `prompts/06-cert-tip-callouts.md` for the full list
- `/generate-module` automatically reads cert tips and inserts them during generation

## Slash Commands

All slash commands are defined as markdown files in `.claude/commands/` and will appear when you type `/` in Claude Code:

| Command | Description |
|---|---|
| `/generate-module M09` | Generate a complete module HTML file |
| `/generate-all-briefs` | Generate brief files for all missing modules + capstones |
| `/generate-capstone CAPSTONE-3 DOMAIN-A` | Generate a capstone project HTML file |
| `/review-module M09` | Review a module against quality standards |
| `/fix-explanations M09` or `/fix-explanations ALL` | Improve explanation quality using depth rules 1-12 |
| `/enhance-animations M09` | Improve animations in an existing module |
| `/build-index` | Regenerate course landing page from completed modules |
| `/consistency-check` | Cross-check all modules for visual consistency |
| `/validate-capstone CAPSTONE-3 DOMAIN-A` | Validate capstone for accuracy and student executability |
| `/generate-lab-repo ALL` | Generate Git-ready lab repo with starter code, solutions, mock data for all modules + capstones |
| `/generate-mobile ALL` | Generate mobile-friendly condensed versions with pseudocode instead of real code |

## Quality Checklist (applied automatically by /generate-module and /review-module)
- [ ] File size < 200KB
- [ ] All CSS/JS inline (external only: Google Fonts, Prism.js CDN)
- [ ] Every H2/H3 has an `id` for sidebar navigation
- [ ] Sticky sidebar navigation present
- [ ] Progress bar shows correct position (e.g., "Module 9 of 30")
- [ ] All technical terms have tooltip definitions on first use
- [ ] At least 3 animated visualizations with play/pause/restart controls
- [ ] `prefers-reduced-motion` media query present
- [ ] Both Python and Node.js code tabs for every code example
- [ ] All code blocks have copy buttons
- [ ] Quiz section: 5+ questions with immediate feedback
- [ ] Previous/Next module navigation links
- [ ] No hardcoded API keys
- [ ] ARIA labels on interactive elements
- [ ] Depth rules applied (analogies unpacked, code annotated, bridges present)
- [ ] Cert tip callouts inserted (if applicable for this module)

