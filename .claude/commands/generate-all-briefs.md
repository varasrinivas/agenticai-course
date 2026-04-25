---
description: Generate module brief files for all modules that don't have one yet
---

Generate individual module brief markdown files for every module that doesn't already have a brief in `prompts/modules/`.

Follow these steps:

1. Scan `prompts/modules/` to find which brief files already exist — SKIP those modules
2. Read `prompts/00-course-philosophy.md` for the course map and track structure
3. Read `prompts/05-module-content-reference.md` for the detailed concept list per module
4. Read ALL existing briefs in `prompts/modules/` (e.g., M01, M02, M05) to learn the exact format:
   - Header: module title, track name, position (N of 30), level, prerequisites, estimated time, track color CSS variable
   - Concepts: 3-5 concepts each with an everyday analogy, technical definition, suggested animation from the catalog in `prompts/01-module-template.md`, and key insight
   - Code walkthrough: What to build and demonstrate
   - Hands-on exercise: Step-by-step with stretch goals
   - Quiz focus: 5 question topics with suggested question types (multiple choice, code completion, etc.)
5. Read `prompts/01-module-template.md` for the animation catalog — assign specific animation patterns to each concept
6. For each missing module, generate a brief file:
   - Filename: `prompts/modules/M{XX}-{slug}.md` (e.g., `M09-rag-retrieval-augmented-generation.md`)
   - Follow the EXACT format of the existing sample briefs
7. Also generate 5 capstone brief files in `prompts/modules/capstones/`:
   - Read `prompts/03-capstone-domains.md` for all domain and project specifications
   - Create `CAPSTONE-1.md` through `CAPSTONE-5.md`
   - Each capstone brief should include: project overview, difficulty rating, skills practiced with module cross-references, all three domain variants (A, B, C), mock data schemas (JSON examples), tool interface definitions, and test case outlines (5 happy path + 3 edge cases + 2 adversarial per domain)
8. Create the `prompts/modules/capstones/` directory if it doesn't exist
9. After generating all files, report:
   - Total module briefs created (out of 21 possible)
   - Total capstone briefs created (out of 5)
   - Files skipped (already existed)
   - Complete list of generated filenames
