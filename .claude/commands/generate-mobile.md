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

1. Read the desktop HTML file from `output/`
2. Extract the core content:
   - The best analogy (Rule 1 content)
   - The main concept explanation (condense to 150-300 words)
   - All code blocks → convert to pseudocode (10-15 lines max, language-agnostic)
   - Common misconceptions (Rule 12 content — take 2-3 best ones)
   - Quiz questions (pick 3 strongest from desktop's 5+)
3. Generate the mobile HTML with 9 swipeable cards:
   - Card 1: Title (module name, track, position "N of 30", "10 min read")
   - Card 2: The Big Idea (ONE paragraph, the core concept)
   - Card 3: The Analogy (best analogy + simple static diagram)
   - Card 4: How It Works (3-5 numbered steps + diagram)
   - Card 5: Pseudocode (language-agnostic, 10-15 lines)
   - Card 6: Common Misconceptions (2-3 with corrections)
   - Card 7: Key Takeaway (2-3 sentence summary box)
   - Card 8: Quick Quiz (3 tap-to-reveal questions)
   - Card 9: Desktop Link ("Ready to build? Open the full module →")
4. Save to `output/mobile/{MODULE_ID}-mobile.html`

## Critical Rules
- Total word count per mobile module: 800-1200 words (desktop is 3000-8000)
- NO real code — only pseudocode using the style from 09-mobile-design.md
- NO lab instructions, setup steps, or troubleshooting
- NO side-by-side Python/Node.js tabs
- ALL diagrams must be under 300px tall
- Touch targets: 44px minimum
- Body font: 16px minimum
- Swipe navigation between cards (CSS scroll-snap)
- Bottom progress bar
- prefers-reduced-motion for any animations
- Dark theme (same as desktop: #0A1628 background)

## After generating ALL mobile modules, also generate:
- `output/mobile/index.html` — mobile course landing page with all modules listed as cards
- Link each card to its mobile module

Report per module: word count, card count, pseudocode blocks, quiz questions
