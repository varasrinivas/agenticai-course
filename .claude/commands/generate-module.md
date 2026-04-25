---
description: Generate a complete module HTML file for the agent course
argument-hint: [MODULE_ID e.g. M01, M09, M14]
---

Generate a complete self-contained interactive HTML module file for module $ARGUMENTS.

Follow these steps in order:

1. Read `prompts/00-course-philosophy.md` for design philosophy
2. Read `prompts/01-module-template.md` for HTML structure and animation catalog
3. Read `prompts/02-visual-design-system.md` for colors, fonts, layout, component CSS
4. Read `prompts/04-quality-standards.md` for content and accessibility rules
5. Read `prompts/07-depth-rules.md` for content depth rules — THIS IS CRITICAL for explanation quality
6. Read `prompts/06-cert-tip-callouts.md` for certification exam tips — check if this module has cert tips that should be inserted
7. Read the module-specific brief: `prompts/modules/$ARGUMENTS-*.md` (glob match on the module ID)
8. If the module brief doesn't exist, read `prompts/05-module-content-reference.md` and find the section for this module
9. Check if previous module exists in `output/` — if so, read it to match visual style and navigation links
10. Generate the complete HTML file to `output/` with filename format `M{XX}-{slug}.html`
11. The HTML must be fully self-contained: all CSS and JS inline, only Google Fonts and Prism.js from CDN
12. CERT TIP INTEGRATION — if `prompts/06-cert-tip-callouts.md` lists cert tips for this module:
    - Insert each cert tip callout box at the appropriate location (after the relevant section, as specified in the file)
    - Use this HTML format for cert tips:
      <div class="callout-cert" style="background:rgba(212,168,67,.06);border-left:4px solid #D4A843;border-radius:0 8px 8px 0;padding:1.25rem 1.5rem;margin:1.5rem 0;">
        <span class="box-label" style="color:#D4A843;">🎓 Cert Tip — Domain X.Y</span>
        <p>{tip content}</p>
      </div>
    - Modules WITHOUT cert tips (M01, M02, M09, M10, M15, M19, M20): skip this step
13. DEPTH CHECK before finalizing — verify every section against depth rules:
    - Every analogy-box has 3+ sentences walking through BEFORE → PAIN → MAPPING
    - Every tech-def-box teaches in plain English, defines sub-terms, explains WHY not just WHAT
    - Every code block is broken into annotated chunks (WHAT/WHY/GOTCHA before each chunk)
    - Every callout-why uses concrete numbers and real scenarios
    - Conceptual bridges exist between major sections (not just heading → content jumps)
    - "What Just Happened?" checkpoints appear after major code blocks
14. HANDS-ON LAB CHECK (Rule 13) — verify the exercise section has:
    - "What You'll Build" one-liner + time estimate + prerequisites
    - Environment setup block (copy-pasteable install command)
    - EVERY step has ALL of: step title, what & why explanation, complete code block, run command, expected output, green checkpoint callout, troubleshooting tips (2-3 common errors)
    - Step dependencies are explicit ("This uses the chunks list from Step 1")
    - Final verification section with end-to-end run command + expected output + congratulations
    - A student following ONLY these instructions can complete the lab without guessing
15. After generating, run the quality checklist:
    - File size < 200KB (deeper explanations = larger files, that's OK)
    - All CSS/JS inline
    - Every H2/H3 has an id for sidebar nav
    - Sticky sidebar navigation present
    - Progress bar shows correct position (e.g., "Module 9 of 30")
    - All technical terms have tooltip definitions on first use
    - At least 3 animated visualizations with play/pause/restart controls
    - prefers-reduced-motion media query present
    - Both Python and Node.js code tabs for every code example
    - All code blocks have copy buttons
    - Quiz section has 5+ questions with immediate feedback
    - Previous/Next module navigation links present
    - No hardcoded API keys
    - ARIA labels on interactive elements
    - Cert tip callouts present (if applicable for this module)
15. Report: file size, section count, animation count, quiz question count, cert tips inserted, estimated reading time
