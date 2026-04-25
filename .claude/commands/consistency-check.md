---
description: Cross-check all generated modules for visual and structural consistency
---

Cross-check all generated modules in `output/` for consistency.

Follow these steps:

1. Scan `output/` for all HTML files
2. For each file, extract and compare:
   - Color palette: Are CSS variables consistent? Any hardcoded colors that should use variables?
   - Typography: Same font families, weights, and sizes across files?
   - Navigation: Sidebar structure matches? Previous/Next links correct and sequential?
   - Quiz format: Same question types, feedback patterns, styling?
   - Animation style: Controls in same position? Same button styling? Same speed defaults?
   - Code tabs: Python/Node.js tabs styled identically? Copy button placement consistent?
   - Section structure: Same ordering (objectives → concepts → code → exercise → quiz → summary)?
   - Progress bar: Correctly numbered for each module's position?
   - Tooltips: Same styling and behavior?
   - Callout boxes: Same colors for analogy, technical, warning, cost callouts?
3. Report inconsistencies with specific file name + line number
4. Group issues by severity: Critical (breaks navigation/layout) vs. Minor (styling differences)
5. Suggest specific fixes for each issue
6. Ask whether to auto-fix
