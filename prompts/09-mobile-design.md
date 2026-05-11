# Mobile Course Design Specification

This spec defines how to generate the MOBILE version of each module — a condensed, phone-friendly format for learning on the go.

## Philosophy
The mobile version is NOT a shrunk desktop version. It's a DIFFERENT learning experience:
- **Desktop**: Deep dives, full code, hands-on labs, 45-90 min per module
- **Mobile**: Core concepts, pseudocode, visual mnemonics, 10-15 min per module

Students use mobile to LEARN CONCEPTS (on the bus, during lunch) and desktop to BUILD (at their desk with a code editor).

## Content Rules

### What to INCLUDE
- Core concept explanation (the "what" and "why") — 3-5 paragraphs max per section
- ONE key analogy per concept (the best one from the desktop version)
- Pseudocode instead of real code (language-agnostic, 10-15 lines max)
- Visual mnemonics (simple SVG diagrams optimized for small screens)
- Key takeaway box at the end of each section
- Quick quiz (3 questions, tap to reveal answer)
- "Learn more on desktop →" links to the full module

### What to EXCLUDE
- Full Python/Node.js code blocks (replaced with pseudocode)
- Hands-on labs and step-by-step exercises (desktop only)
- Environment setup instructions
- Troubleshooting guides
- Expected terminal output blocks
- Side-by-side language tabs (Python/Node.js)
- Complex multi-step animations (replaced with static diagrams or simple 2-3 frame animations)

### Pseudocode Style
NOT this (real code):
```python
import anthropic
client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=[{
        "name": "search_filings",
        "description": "Search UCC filings by debtor name",
        "input_schema": {
            "type": "object",
            "properties": {
                "debtor_name": {"type": "string"},
                "state": {"type": "string"}
            },
            "required": ["debtor_name"]
        }
    }],
    messages=[{"role": "user", "content": query}]
)
```

YES this (pseudocode):
```
DEFINE tool "search_filings"
  input: debtor_name (required), state (optional)
  returns: list of matching UCC filings

SEND to Claude:
  model: sonnet
  tools: [search_filings]
  message: user's question

IF Claude returns tool_use:
  RUN the requested tool
  SEND results back to Claude
  REPEAT until Claude returns final answer
```

### Section Length
- Desktop section: 500-1000 words
- Mobile concept cluster: 400-600 words per concept (each major desktop concept gets its own cluster — see "Module Structure" below)
- Rule: if you can't explain ONE concept in 600 mobile words, you're including implementation detail that belongs on desktop
- Total mobile module length scales with desktop concept count: 1-concept module ≈ 600 words, 6-concept module ≈ 3600 words. Mobile should still come in ~50% shorter than the equivalent desktop module — never collapse multiple desktop concepts into a single mobile cluster.

## Visual Design (Mobile-Specific)

### Layout
- Single column, full width
- No sidebar navigation (use bottom tab bar or swipe between sections)
- Font size: 16px minimum body text (no squinting)
- Tap targets: 44px minimum (Apple HIG)
- Sections as swipeable cards (swipe left/right between sections)

### CSS Variables (extend the desktop design system)
```css
:root {
    /* Inherit all desktop vars, override these: */
    --mobile-max-width: 100vw;
    --mobile-padding: 1rem;
    --mobile-font-body: 16px;
    --mobile-font-heading: 22px;
    --mobile-card-gap: 0.75rem;
    --mobile-code-font: 14px;
    --mobile-quiz-tap-size: 44px;
}

/* Card-based sections */
.mobile-card {
    background: rgba(255, 255, 255, 0.03);
    border-radius: 12px;
    padding: 1.25rem;
    margin: 0.75rem 0;
    scroll-snap-align: start;
}

/* Pseudocode blocks */
.pseudocode {
    background: rgba(99, 102, 241, 0.08);
    border-left: 3px solid var(--track-color);
    border-radius: 0 8px 8px 0;
    padding: 1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    line-height: 1.6;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}

/* Key takeaway box */
.takeaway {
    background: rgba(212, 168, 67, 0.08);
    border: 1px solid rgba(212, 168, 67, 0.3);
    border-radius: 12px;
    padding: 1rem;
    margin: 1rem 0;
}
.takeaway::before {
    content: "💡 Key Takeaway";
    display: block;
    font-weight: 700;
    color: #D4A843;
    margin-bottom: 0.5rem;
}

/* Tap-to-reveal quiz */
.quiz-card {
    background: rgba(255, 255, 255, 0.04);
    border-radius: 12px;
    padding: 1.25rem;
    cursor: pointer;
    min-height: 44px;
}
.quiz-card .answer {
    display: none;
    margin-top: 0.75rem;
    padding-top: 0.75rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
}
.quiz-card.revealed .answer {
    display: block;
}
```

### Animations
- Replace complex multi-step animations with STATIC diagrams or simple 2-3 frame animations
- Use CSS transitions (not keyframe animations) for smooth mobile performance
- All animations respect prefers-reduced-motion
- Touch-friendly: tap to advance frames instead of play/pause controls
- Max animation size: 300px tall (visible without scrolling on most phones)

### Navigation
- Bottom progress bar showing current section / total sections
- Swipe left/right between sections (CSS scroll-snap)
- "Previous Module ← | → Next Module" at the bottom
- Floating "☰" menu button for jump-to-section

## Module Structure (Mobile Version)

A mobile module is composed of swipeable cards in this order:

1. **Title Card** (1, always) — Module name, track, position ("5 of 30"), time estimate
2. **Concept Index Card** (1, always) — Tap-to-jump list of every concept cluster in this module
3. **Concept Clusters** (1 per major desktop concept — see "How to identify concepts" below)
4. **Quick Quiz Card** (1, shared) — 3-5 tap-to-reveal questions covering the strongest insight from each concept
5. **Desktop Link Card** (1, always) — "Ready to build? Open the full module on desktop →"

### How to identify "major concepts" in a desktop module

A "concept" is a top-level `<h2>` in the desktop HTML, EXCLUDING administrative/scaffolding sections:
- Learning Objectives
- Hands-On Exercise / Lab
- Knowledge Check / Quiz
- Module Summary
- References & Resources
- Code Walkthrough sections that are step-by-step implementations of an already-introduced concept (fold their key idea into the parent concept's pseudocode card; do NOT make them their own cluster)

Every other `<h2>` becomes ONE concept cluster on mobile. **You must produce one cluster per concept — never collapse multiple desktop concepts into a single mobile cluster.** A learner who only reads mobile must encounter every major concept the desktop teaches, even if at lower depth.

Example concept inventories:
- **M02 Tokens** (1 concept): Tokens. → 1 cluster.
- **M09 RAG** (6 concepts): RAG basics, Embeddings, Chunking, Vector DBs, Citations, Multimodal. → 6 clusters.
- **M12 ReAct** (7 concepts): Pattern landscape, ReAct loop, Implementation, Thought Traces, Stop Conditions, Error Handling, Extended Thinking. → 7 clusters.
- **M16 Input Guardrails** (5 concepts): Why guardrails, PII Detection, Prompt Injection, Schema Validation, Rate Limiting. → 5 clusters.
- **M19 Tracing** (7 concepts): Why observability, Traces, Spans, Structured Logging, Tools landscape, Compliance, Prompt Versioning. → 7 clusters.
- **M26 Agent SDK** (7 concepts): Why SDK, Build agent, Hooks, Sessions, Subagents, Production stack, When to leave SDK. → 7 clusters.

### Concept Cluster — 5 cards per concept

For each major concept, generate this 5-card cluster (in order):

1. **Big Idea** — H2 = the concept's name. One paragraph (2-4 sentences) explaining ONLY this concept's core idea. If the learner reads nothing else from this cluster, they get the point.
2. **Analogy** — The best analogy from the desktop content for THIS concept (BEFORE → PAIN → MAPPING per Rule 11). Add a small visual if it helps.
3. **How It Works** — 3-5 numbered steps + a static or simple 2-3 frame diagram. Specific to THIS concept.
4. **Pseudocode OR Decision Framework** — 10-15 lines. For algorithmic concepts, language-agnostic pseudocode. For non-algorithmic concepts ("Why X matters", "When to use Y"), substitute a decision framework, anti-pattern list, or comparison table.
5. **Misconceptions + Takeaway** — 1-2 misconceptions specific to THIS concept (❌ wrong → ✅ right) followed by a 💡 Key Takeaway box (2-3 sentences).

### Card numbering and progress bar

The bottom progress bar shows `current / total` where total = `2 + (5 × concept_count) + 2`. Each card scroll-snaps to viewport. Concept clusters carry a small `Concept N of M` chip in the top corner so the learner knows where they are inside the module.

## File Naming
- Desktop: `output/M09-rag.html`
- Mobile: `output/mobile/M09-rag-mobile.html`

## Responsive Behavior
- Mobile version is a SEPARATE file (not a responsive desktop file)
- The desktop index page links to mobile versions with "📱 Mobile version" badges
- The mobile index page is `output/mobile/index.html`

## Example: M09 RAG (Mobile Version)

M09 has 6 major desktop concepts → 6 clusters → 34 cards total (1 title + 1 index + 6×5 + 1 quiz + 1 desktop link).

### Card 1: Title
```
MODULE 9 of 30
RAG — Retrieval-Augmented Generation
Track 3: Memory & Context
⏱ 25 min read · 6 concepts
```

### Card 2: Concept Index
```
What you'll learn (tap to jump):
  1. RAG basics — search + generate
  2. Embeddings — turning text into searchable numbers
  3. Chunking — slicing documents the right way
  4. Vector databases — where embeddings live
  5. Citations — Claude's native provenance
  6. Multimodal inputs — PDFs, images, Files API
```

### Cluster 1 — Concept: RAG basics (Cards 3-7)

**Card 3 — Big Idea:** "Claude's training data has a cutoff — it doesn't know YOUR documents. RAG solves this by SEARCHING your documents and pasting the relevant parts into Claude's prompt before it answers."

**Card 4 — Analogy:** "Open-book exam. The student (Claude) doesn't memorize the textbook — they flip to the most relevant pages before answering each question."
[Diagram: Question → Search → Find pages → Paste into prompt → Claude answers]

**Card 5 — How It Works:** 1. PREPARE (once): split docs, embed, store. 2. SEARCH (per question): embed query, find nearest chunks. 3. GENERATE: paste chunks into prompt.

**Card 6 — Pseudocode:**
```
FOR each document:
  chunks = SPLIT into 500-word pieces
  FOR each chunk: STORE(EMBED(chunk), chunk)

query_emb = EMBED(user_question)
top_3 = SEARCH vector_db nearest to query_emb
ASK Claude("Use this context: " + top_3 + user_question)
```

**Card 7 — Misconceptions + Takeaway:** ❌ "RAG = fine-tuning" → No, RAG just adds text to the prompt. ❌ "RAG eliminates hallucinations" → Reduces, not eliminates. 💡 RAG = search + generate, no model changes needed.

### Cluster 2 — Concept: Embeddings (Cards 8-12)

**Card 8 — Big Idea:** "An embedding is a list of ~1500 numbers that represents the *meaning* of a piece of text. Similar meanings → similar numbers → close in vector space."

**Card 9 — Analogy:** "Map coordinates for ideas. The word 'dog' and 'puppy' end up at nearby coordinates; 'dog' and 'spreadsheet' end up far apart. Search = find the nearest coordinates to your question."

**Card 10 — How It Works:** Embedding model reads text → outputs fixed-size vector → cosine similarity measures distance → smaller distance = more relevant.

**Card 11 — Pseudocode:** [embedding flow with cosine similarity]

**Card 12 — Misconceptions + Takeaway:** ❌ "Bigger embedding = better" → Diminishing returns past ~1500 dims. 💡 Embeddings are how machines turn meaning into math.

### Cluster 3 — Concept: Chunking (Cards 13-17)
[Same 5-card structure for chunk size strategies, overlap, semantic vs fixed]

### Cluster 4 — Concept: Vector Databases (Cards 18-22)
[Same 5-card structure for ChromaDB / Pinecone / pgvector, indexing, hybrid search]

### Cluster 5 — Concept: Citations (Cards 23-27)
[Same 5-card structure for Claude's native citations API, when to use vs RAG]

### Cluster 6 — Concept: Multimodal Inputs (Cards 28-32)
[Same 5-card structure for PDFs, vision, Files API, decision matrix]

### Card 33 — Quick Quiz (one question per concept)
Q: Does RAG change Claude's model weights? → No, only the prompt.
Q: Why are embeddings ~1500 numbers, not 5? → Need enough dimensions to separate meanings.
Q: What's the risk of 2000-word chunks? → Dilution: relevant sentence gets lost.
Q: When pick Citations over RAG? → When you must prove which source supported each sentence.
Q: Files API vs base64 PDFs? → Files API for repeated reuse; base64 for one-off.

### Card 34 — Desktop Link
"Ready to build a real RAG pipeline? Open the full module on desktop →"
