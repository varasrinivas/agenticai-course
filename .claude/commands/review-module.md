---
description: Review an existing module HTML file against quality standards
argument-hint: [MODULE_ID e.g. M01, M09]
---

Review the generated module $ARGUMENTS against all quality standards.

Follow these steps:

1. Find and read the module HTML from `output/` (glob match on $ARGUMENTS)
2. Read `prompts/04-quality-standards.md` for the full quality checklist
3. Check every item and report as a numbered checklist with pass/fail and line numbers:
   - [ ] File size < 150KB
   - [ ] All CSS inline (no external stylesheets except CDN)
   - [ ] All JS inline (no external scripts except CDN)
   - [ ] Google Fonts loaded from CDN
   - [ ] Syntax highlighting library loaded from CDN
   - [ ] Every H2/H3 has an `id` attribute for sidebar navigation
   - [ ] Sticky sidebar navigation present and functional
   - [ ] Progress bar shows correct module position
   - [ ] All technical terms have tooltip definitions on first use (list any missing)
   - [ ] At least 3 animated visualizations
   - [ ] All animations have play/pause/restart controls
   - [ ] `prefers-reduced-motion` media query present
   - [ ] Both Python and Node.js code tabs for every code example
   - [ ] All code blocks have copy buttons
   - [ ] Quiz section has 5+ questions with immediate feedback
   - [ ] Previous/Next module navigation links present and correct
   - [ ] No hardcoded API keys
   - [ ] All external links have `target="_blank" rel="noopener noreferrer"`
   - [ ] ARIA labels on interactive elements
   - [ ] Code examples are complete and runnable (not pseudocode)
   - [ ] Error handling present in code examples
4. Summarize: total checks passed / total checks, and list all failures
5. Ask whether to auto-fix the failures
