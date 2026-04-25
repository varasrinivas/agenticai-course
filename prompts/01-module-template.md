# Module HTML Template & Animation Catalog

## HTML Structure

Every module MUST contain these sections in this order:

### 1. COURSE HEADER
- Course title, track name, module number and title
- Progress indicator showing position in curriculum (e.g., "Module 9 of 30")
- Estimated completion time
- Prerequisites (which modules must be completed first)

### 2. LEARNING OBJECTIVES
- 3-5 specific, measurable objectives
- Skill level indicator (Beginner / Intermediate / Advanced)

### 3. CONCEPT EXPLAINERS (for each concept in the module)
- **"Everyday Analogy" box** — explain the concept using a real-world metaphor
- **"Technical Definition" box** — precise technical explanation
- **ANIMATED VISUAL** — CSS/JS animation illustrating the concept
  - Use smooth, educational animations (not flashy/distracting)
  - Include play/pause/step controls for complex animations
  - Add annotations that appear at key animation moments
- **"Why It Matters" callout** — practical impact statement
- **Interactive sandbox** (where applicable) — let the learner experiment

### 4. CODE WALKTHROUGHS
- Side-by-side: code on left, animated explanation on right
- Line-by-line highlighting with explanations
- "Run" button to execute in an embedded sandbox (where possible)
- Both Python AND Node.js/TypeScript versions via tabbed panels
- Copy button for all code blocks

### 5. HANDS-ON EXERCISE
- Step-by-step instructions with checkpoints
- Starter code template
- Expected output examples
- Common mistakes and troubleshooting guide
- "Stretch goals" for advanced learners

### 6. KNOWLEDGE CHECK
- 5 interactive quiz questions (mix of: multiple choice, drag-and-drop, code completion)
- Immediate feedback with explanations for wrong answers
- Confidence meter — learner rates their understanding

### 7. MODULE SUMMARY
- Key concepts recap (visual cheat sheet)
- "What we built" — screenshot/diagram of the hands-on result
- "Next module preview" — what's coming and why it builds on this

### 8. REFERENCE SIDEBAR
- Official Claude API documentation links
- Related Anthropic cookbook examples
- External resources (papers, videos, tools)


## Animation Catalog

Use these reusable animation patterns. Each animation MUST have play/pause/restart controls and a `prefers-reduced-motion` fallback.

| Pattern Name | Description | Use In |
|---|---|---|
| `TOKEN_FLOW` | Text enters left, splits into colored token blocks, flows right | M02, M08 |
| `CONTEXT_WINDOW` | Rectangular area fills with blocks; oldest blocks fade when full | M02, M08 |
| `EMBEDDING_SPACE` | 3D-ish scatter plot with vectors; similarity shown via proximity | M09, M10 |
| `TOOL_LOOP` | Circular flow diagram with steps highlighting in sequence | M05, M06 |
| `DAG_EXECUTION` | Nodes + edges with data flowing along paths; parallel paths animate simultaneously | M06, M13 |
| `REACT_LOOP` | Circular Reason→Act→Observe cycle with thought bubbles appearing | M12 |
| `MEMORY_TIERS` | Stacked layers with data flowing between them | M11 |
| `PIPELINE_FLOW` | Left-to-right data transformation with stages | M09, M10, M16 |
| `GUARDRAIL_CHECK` | Data passes through checkpoints; some blocked (red), some pass (green) | M16, M17 |
| `TRACE_WATERFALL` | Nested horizontal bars showing timing of operations | M19 |
| `COST_BREAKDOWN` | Animated stacked bar chart showing cost components | M22 |
| `AGENT_CONVERSATION` | Message bubbles appearing in sequence showing multi-turn interaction | M03, M08, M12 |
| `MCP_HANDSHAKE` | Client ↔ Server protocol frames with highlighted message types | M07 |
| `MULTI_AGENT_FLOW` | Multiple agent boxes passing messages between them | M14 |
| `CIRCUIT_BREAKER` | Counter incrementing; at threshold, circuit trips and traffic reroutes | M17 |

### Animation Implementation Rules
- All animations: CSS + vanilla JS only (no external animation libraries)
- Use `requestAnimationFrame` for smooth rendering
- Use `transform` and `opacity` for GPU-accelerated performance
- Keep all animations under 60fps
- Provide static SVG fallback for `prefers-reduced-motion`
- Animation controls: play ▶, pause ⏸, restart ↻, step forward ⏭ (for multi-step)
- Annotations: Use absolutely-positioned labels that appear/disappear at animation keyframes
