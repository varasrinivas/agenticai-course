---
description: Generate a capstone project HTML file
argument-hint: [CAPSTONE_ID DOMAIN e.g. CAPSTONE-3 DOMAIN-A]
---

Generate a complete capstone project HTML file for $ARGUMENTS.

Parse the arguments: first word is the capstone ID (e.g., CAPSTONE-3), second word is the domain (e.g., DOMAIN-A, DOMAIN-B, or DOMAIN-C). If no domain is specified, generate a comparison table of all three domain variants first, then ask which to generate.

Follow these steps:

1. Read `prompts/00-course-philosophy.md` for design philosophy
2. Read `prompts/01-module-template.md` for HTML structure and animation catalog
3. Read `prompts/02-visual-design-system.md` for colors, fonts, layout
4. Read `prompts/04-quality-standards.md` for content and accessibility rules
5. Read `prompts/07-depth-rules.md` for explanation depth rules (especially Rules 13-14 for lab steps and capstone packets)
6. Read `prompts/08-capstone-animations.md` for architecture diagrams and animation specs for THIS capstone
7. Read `prompts/03-capstone-domains.md` for domain context and project specifications
8. Read `prompts/06-cert-tip-callouts.md` for any cert tips applicable to this capstone's concepts
9. If it exists, read the capstone-specific brief: `prompts/modules/CAPSTONE-{N}*.md`
10. Check prerequisite modules in `output/` for style consistency
11. Generate the HTML file with:
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
    - Local production deployment (Tier 1: Docker + DuckDB — no cloud account needed)
    - Rancher Desktop alternative callout: "Using Rancher Desktop instead of Docker? If you chose dockerd runtime, all commands work as-is. If containerd, replace docker with nerdctl. See prompts/10-rancher-deployment.md for details."
    - Cloud deployment option (Tier 2: GCP or Tier 3: AWS — for students with access)
    - Compliance callouts (HIPAA for Domain A, PCI-DSS/EDI for Domain B, state filing regs for Domain C)
    - Cert tip callouts where applicable
    - "Going Further" extensions marked as OPTIONAL
12. Save to `output/CAPSTONE-{N}-DOMAIN-{A|B|C}.html`
13. QUALITY CHECK:
    - Architecture diagram present and animated
    - All animations from 08-capstone-animations.md included with play/pause/restart controls
    - prefers-reduced-motion fallbacks for every animation
    - Every build step has ALL Rule 13 components (code/run/output/checkpoint/troubleshooting)
    - Mock data is complete and realistic (not placeholder)
    - Code is copy-paste-runnable (no TODOs, no missing imports)
    - Local production mode (Tier 1) included — student doesn't need a cloud account
14. Report: file size, animation count, build step count, test scenario count, estimated completion time
