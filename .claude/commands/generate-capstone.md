---
description: Generate a capstone project HTML file
argument-hint: [CAPSTONE_ID DOMAIN e.g. CAPSTONE-3 DOMAIN-A]
---

Generate a complete capstone project HTML file for $ARGUMENTS.

Parse the arguments: first word is the capstone ID (e.g., CAPSTONE-3), second word is the domain (e.g., DOMAIN-A, DOMAIN-B, or DOMAIN-C). If no domain is specified, generate a comparison table of all three domain variants first, then ask which to generate.

Follow these steps:

1. Read `prompts/19-sdk-tier-policy.md` FIRST and look up this capstone in the Per-Module
   Tier Index. It decides which API surface the solution uses, and getting it wrong is a
   critical finding in `/validate-capstone`. Tier 3 additionally requires a
   `spec/agent-spec.md` following `prompts/17-spec-driven-development.md`, and an HTML
   section walking read spec -> generate -> diff against `solution/` -> iterate
2. Read `prompts/00-course-philosophy.md` for design philosophy
3. Read `prompts/01-module-template.md` for HTML structure and animation catalog
4. Read `prompts/02-visual-design-system.md` for colors, fonts, layout
5. Read `prompts/04-quality-standards.md` for content and accessibility rules
6. Read `prompts/07-depth-rules.md` for explanation depth rules (especially Rules 13-14 for lab steps and capstone packets)
7. Read `prompts/08-capstone-animations.md` for architecture diagrams and animation specs for THIS capstone
8. Read `prompts/03-capstone-domains.md` for domain context and project specifications
9. Read `prompts/06-cert-tip-callouts.md` for any cert tips applicable to this capstone's concepts
10. If it exists, read the capstone-specific brief: `prompts/modules/CAPSTONE-{N}*.md`
11. Check prerequisite modules in `output/courses/claude-agents/` for style consistency
12. Generate the HTML file with:
    - Architecture diagram FIRST (animated SVG as specified in 08-capstone-animations.md) — student sees the blueprint before building
    - ALL animations specified for this capstone in 08-capstone-animations.md (hero animation, supporting animations, interactive elements)
    - Project brief with business context and industry background
    - Domain glossary of key terms
    - Mock data specification with complete, realistic sample JSON structures
    - File structure diagram (interactive, click to see file descriptions)
    - Step-by-step build guide following Rule 13 EXACTLY:
      * Every step has: title, what & why, file instruction, COMPLETE code, run command, expected output, checkpoint, troubleshooting
      * Step dependencies explicit ("This uses X from Step 3")
      * Final verification section with end-to-end run + expected output
    - Test scenarios with specific inputs, expected behaviors, and expected outputs
    - Local production deployment (**deployment** tier 1: Docker + DuckDB, no cloud account needed)
    - Rancher Desktop alternative callout: "Using Rancher Desktop instead of Docker? If you chose dockerd runtime, all commands work as-is. If containerd, replace docker with nerdctl. See prompts/10-rancher-deployment.md for details."
    - Cloud deployment option (**deployment** tiers 2 and 3: GCP, AWS — for students with access).
      NOTE: these are deployment tiers and have nothing to do with the SDK tiers in
      `19-sdk-tier-policy.md`. A Tier 3 SDK capstone can ship a deployment-tier-1 lab
    - Compliance callouts (HIPAA for Domain A, PCI-DSS/EDI for Domain B, state filing regs for Domain C)
    - Cert tip callouts where applicable
    - "Going Further" extensions marked as OPTIONAL
13. Save to `output/courses/claude-agents/CAPSTONE-{N}-DOMAIN-{A|B|C}.html`.
    Standalone capstones use a slug instead of a domain letter, e.g.
    `CAPSTONE-9-behavioral-health-modernization.html`. The lab goes in
    `labs/capstone-{n}-{slug}/`. Then rebuild the search index:
    `node scripts/build-search-assistant.mjs claude-agents`
14. QUALITY CHECK:
    - Architecture diagram present and animated
    - All animations from 08-capstone-animations.md included with play/pause/restart controls
    - prefers-reduced-motion fallbacks for every animation
    - Every build step has ALL Rule 13 components (code/run/output/checkpoint/troubleshooting)
    - Mock data is complete and realistic (not placeholder)
    - Code is copy-paste-runnable (no TODOs, no missing imports)
    - Local production mode (deployment tier 1) included — student doesn't need a cloud account
15. Report: file size, animation count, build step count, test scenario count, estimated completion time
