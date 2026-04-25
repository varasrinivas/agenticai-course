---
description: Improve and upgrade animations in an existing module
argument-hint: [MODULE_ID e.g. M09]
---

Improve the animations in module $ARGUMENTS.

Follow these steps:

1. Read the module HTML from `output/` (glob match on $ARGUMENTS)
2. Read `prompts/01-module-template.md` for the animation catalog and implementation rules
3. Identify all existing animations in the file
4. For each animation, evaluate:
   - Is it static when it should be animated?
   - Does it have play/pause/restart controls?
   - Does it have step-forward controls for multi-step animations?
   - Are there annotations that appear at key animation moments?
   - Is it using CSS transform/opacity for GPU acceleration?
   - Does it respect `prefers-reduced-motion` with a static fallback?
   - Is the timing appropriate (not too fast, not too slow)?
5. Upgrade animations that are too simple or missing features
6. Add annotations (absolutely-positioned labels) at key moments
7. Ensure all animations use `requestAnimationFrame` for smooth rendering
8. Verify `prefers-reduced-motion` fallbacks exist for every animation
9. Report: animations found, animations upgraded, new features added
