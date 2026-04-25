---
description: Generate the course landing page (index.html) from all completed modules
---

Regenerate the `index.html` course landing page.

Follow these steps:

1. Read `prompts/02-visual-design-system.md` for colors, fonts, and layout
2. Scan `output/` for all generated module and capstone HTML files
3. Generate `output/index.html` with:
   - Course title: "Building AI Agents with Claude: From Hello World to Autonomous Production Systems"
   - Course description and what learners will build
   - 8 tracks displayed as sections, each with its signature color
   - Module cards within each track showing: title, level, estimated time, completion status
   - Link to each completed module's HTML file
   - Greyed-out cards for modules not yet generated
   - Three learning path recommendations:
     - Path A: "Weekend Builder" (fastest path to building an agent)
     - Path B: "Deep Diver" (comprehensive understanding)
     - Path C: "Production Engineer" (focus on reliability and deployment)
   - Prerequisites map showing module dependencies
   - Progress tracker (X of 30 modules complete)
   - Responsive design matching the course visual system
4. Report: total modules found, tracks with content, completion percentage
