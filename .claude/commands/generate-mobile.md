---
description: Generate a mobile-friendly condensed version of a module with pseudocode instead of real code
argument-hint: [MODULE_ID or ALL e.g. M09, M15B, ALL]
---

Generate the mobile version of module(s): $ARGUMENTS

If $ARGUMENTS is "ALL", generate mobile versions for every module that has a desktop HTML in output/.
If a specific module, generate just that one.

Read these files first:
- `prompts/09-mobile-design.md` — mobile design spec (REQUIRED — contains layout, pseudocode rules, card structure)
- `prompts/02-visual-design-system.md` — base colors and typography to extend
- `prompts/07-depth-rules.md` — for analogy and misconception content to pull from

Then read the DESKTOP version of the module from `output/{MODULE_ID}*.html` to extract content.

## Generation Process

For each module:

1. Read the desktop HTML file from `output/`.
2. **Inventory concepts** — list every top-level `<h2>` in the desktop HTML, then EXCLUDE administrative sections (see 09-mobile-design.md for the full exclusion list). Each remaining `<h2>` becomes one concept cluster on mobile. **Never collapse multiple desktop concepts into one mobile cluster** — if the desktop teaches 6 concepts, mobile must teach 6 concepts.
3. For each concept, extract from the desktop content:
   - The best analogy (Rule 1 / Rule 11 content) for THAT concept
   - The core explanation (condense to 2-4 sentences)
   - The most representative code → convert to pseudocode (10-15 lines, language-agnostic). For non-algorithmic concepts substitute a decision framework or comparison table.
   - 1-2 misconceptions (Rule 12 content) specific to that concept
   - One strong quiz question that tests the concept's core insight
4. Generate the mobile HTML with this card sequence:
   - **Card 1: Title** — module name, track, position ("N of 30"), time estimate ("X min read · Y concepts")
   - **Card 2: Concept Index** — tap-to-jump list of every concept cluster
   - **Concept Clusters** (5 cards per concept, in desktop order):
     - Big Idea (one paragraph, this concept only)
     - Analogy (BEFORE → PAIN → MAPPING)
     - How It Works (3-5 numbered steps + diagram)
     - Pseudocode OR Decision Framework (10-15 lines)
     - Misconceptions (1-2) + 💡 Key Takeaway box
   - **Penultimate Card: Quick Quiz** — 3-5 tap-to-reveal questions, one per concept where possible
   - **Last Card: Desktop Link** — "Ready to build? Open the full module on desktop →"
5. Save to `output/mobile/{MODULE_ID}-mobile.html`

Concept-cluster cards must include a small `Concept N of M` chip in the top corner so swipers know where they are inside the module.

## Critical Rules
- Per concept cluster: 400-600 words. Total mobile module word count = ~500 + (concept_count × 500). A 6-concept module ≈ 3500 words mobile vs 6000-8000 desktop.
- One mobile concept = one desktop H2. Do NOT merge concepts to fit a smaller card count.
- NO real code — only pseudocode using the style from 09-mobile-design.md
- NO lab instructions, setup steps, or troubleshooting
- NO side-by-side Python/Node.js tabs
- ALL diagrams must be under 300px tall
- Touch targets: 44px minimum
- Body font: 16px minimum
- Swipe navigation between cards (CSS scroll-snap)
- Bottom progress bar shows `current / total` where total = 2 + (5 × concept_count) + 2
- prefers-reduced-motion for any animations
- Dark theme (same as desktop: #0A1628 background)

## After generating ALL mobile modules, also generate:
- `output/mobile/index.html` — mobile course landing page with all modules listed as cards
- Link each card to its mobile module

Report per module: concept count (= number of concept clusters generated), total card count, total word count, pseudocode blocks, quiz questions. Flag any concept where the desktop H2 was excluded so the user can confirm the inventory.
