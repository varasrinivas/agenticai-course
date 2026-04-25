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
- Mobile section: 150-300 words (same concept, 70% shorter)
- Rule: if you can't explain it in 300 words, you're including implementation detail that belongs on desktop

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

Each mobile module has these sections (as swipeable cards):

1. **Title Card** — Module name, track, position (e.g., "5 of 30"), time estimate ("10 min read")
2. **The Big Idea** — ONE paragraph explaining the core concept. If a student reads nothing else, they get the point from this.
3. **The Analogy** — The best analogy from the desktop version, with a simple visual
4. **How It Works** — 3-5 step explanation with a static or simple animated diagram
5. **The Pseudocode** — Language-agnostic pseudocode showing the key pattern (10-15 lines max)
6. **Common Misconceptions** — 2-3 wrong mental models with corrections (from desktop Rule 12)
7. **Key Takeaway** — 2-3 sentence summary box
8. **Quick Quiz** — 3 tap-to-reveal questions
9. **Desktop Link** — "Ready to build? Open the full module on desktop →"

## File Naming
- Desktop: `output/M09-rag.html`
- Mobile: `output/mobile/M09-rag-mobile.html`

## Responsive Behavior
- Mobile version is a SEPARATE file (not a responsive desktop file)
- The desktop index page links to mobile versions with "📱 Mobile version" badges
- The mobile index page is `output/mobile/index.html`

## Example: M09 RAG (Mobile Version)

### Card 1: Title
```
MODULE 9 of 30
RAG — Retrieval-Augmented Generation
Track 3: Memory & Context
⏱ 10 min read
```

### Card 2: The Big Idea
"Claude's training data has a cutoff — it doesn't know YOUR documents. RAG solves this by SEARCHING your documents and pasting the relevant parts into Claude's prompt before it answers. Think of it as giving Claude a cheat sheet customized for each question."

### Card 3: The Analogy
"Imagine an open-book exam. The student (Claude) doesn't memorize the textbook — instead, before answering each question, they flip to the most relevant pages and read those. RAG is the page-flipping step."

[Simple diagram: Question → Search → Find pages → Paste into prompt → Claude answers]

### Card 4: How It Works
1. **PREPARE** (once): Split your documents into small pieces. Convert each piece into a number-array (embedding). Store in a searchable database.
2. **SEARCH** (every question): Convert the user's question into the same kind of number-array. Find the 3 closest document pieces.
3. **GENERATE**: Paste those 3 pieces into Claude's prompt alongside the question. Claude answers using the provided context.

### Card 5: Pseudocode
```
// SETUP (run once)
FOR each document:
  chunks = SPLIT document into 500-word pieces
  FOR each chunk:
    embedding = EMBED(chunk)  // numbers representing meaning
    STORE(embedding, chunk) in vector database

// QUERY (run per question)
query_embedding = EMBED(user_question)
top_3_chunks = SEARCH vector database for nearest to query_embedding
prompt = "Answer using ONLY this context: " + top_3_chunks + user_question
response = ASK Claude with prompt
```

### Card 6: Misconceptions
❌ "RAG = fine-tuning" → No. Fine-tuning changes the model ($$$, weeks). RAG just adds text to the prompt.
❌ "Bigger chunks = better" → Usually opposite. A 2000-word chunk dilutes the relevant sentence.
❌ "RAG eliminates hallucinations" → Reduces them, doesn't eliminate. Claude can still misinterpret context.

### Card 7: Takeaway
💡 RAG is search + generate. You search your documents for relevant pieces, paste them into the prompt, and let Claude answer from that context. No model changes needed.

### Card 8: Quiz
Q: Does RAG change Claude's model weights?
[tap] No — it only changes what's in the prompt.

Q: Why split documents into chunks?
[tap] Embedding models have token limits, and smaller chunks give more precise search results.

Q: What's the main risk of RAG?
[tap] Claude can still hallucinate even with context — RAG reduces but doesn't eliminate this.
