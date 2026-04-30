# M03B: Context Engineering — Curating What the Model Sees

**Track**: 1 — Foundations | **Position**: After M03, before M04
**Prerequisites**: M01, M02, M03
**Estimated Time**: 50-60 minutes
**Level**: Beginner → Intermediate
**Track Color**: var(--track-foundations) / #6366F1

## Why This Module Must Exist
M03 teaches **prompt engineering** — how to author the message you send. But every later module (M07 tools, M08 history, M09–10 RAG, M11 memory, M14 subagents, M22 caching) keeps adding new things to what the model actually sees on each turn: tool definitions, prior messages, retrieved chunks, tool results. Without a single anchor that names this curation as a discipline, learners arrive at M08 and M09 trying to fix symptoms (truncation errors, lost-in-the-middle, ballooning token bills) without the framework that explains why those symptoms happen.

This module gives that anchor. Prompt engineering = writing the message. **Context engineering = curating everything the model sees at turn N, under a finite budget.** Every later module either *adds* to the context (tools, retrieval, memory) or *manages* it (compaction, caching, offload). Learners need this map before they start adding pieces in M04.

## Concepts

### 1. The "What Does the Model Actually See?" Inventory
Every API call assembles a stack: system prompt + tool definitions + conversation history + retrieved documents + tool results + current user turn. Most learners only think about the last item. The animated stack shows all six layers with a live token meter, so the learner *sees* that the user message is often <5% of what gets sent.

- **Analogy**: Court evidence binder. The prompt is the closing argument; the binder is everything else the jury reads. Lawyers spend more time curating the binder than writing the argument.
- **Animation**: Stacked layers slide into a "context window" frame, each with its token cost. A counter ticks up as layers stack.
- **Key insight**: The model has no privileged access to "the question." Every byte competes for the same window.

### 2. The Four Levers — Add, Compress, Retrieve, Offload
Every context-engineering decision is one of four moves: **add** (include it directly), **compress** (summarize/trim), **retrieve** (fetch only when relevant), **offload** (push to a subagent or external store). This is the organizing frame the rest of Track 3 operationalizes.

- **Analogy**: Packing for a trip. Add = put in the bag. Compress = use packing cubes. Retrieve = ship ahead and pick up at hotel. Offload = leave with a friend.
- **Animation**: A single "fact" travels through each lever, showing where it lives and what the model sees in each case.
- **Key insight**: There's no universal right answer — the lever depends on access frequency, freshness needs, and token cost.

### 3. Static vs. Dynamic Context (and Why Caching Cares)
System prompt and tool definitions are *static* across a conversation. History and retrieved docs are *dynamic*. This split is what makes prompt caching (M22) work — and why putting dynamic content before static content destroys the cache. Sets up M22 with a concrete reason, not just "caching is cheaper."

- **Analogy**: Restaurant menu vs. order ticket. Menu is printed once, ticket is written per customer. If you reprint the menu every order, you're wasting paper.
- **Animation**: Two side-by-side conversations, one with static-first ordering (cache hits visualized in green), one with dynamic-first (cache miss in red). Token cost ticker.
- **Key insight**: Order matters as much as content.

### 4. Position Effects — Lost in the Middle
Models attend more strongly to the start and end of the context window than the middle. The same fact at position 1 vs. position 50 produces different answers. This isn't a bug to fix — it's a constraint to design around.

- **Analogy**: Meeting agenda. People remember the opening goal and the closing action items; bullet point #14 of 23 is forgotten.
- **Animation**: Same haystack, same needle, three positions (start/middle/end) with model accuracy bar for each.
- **Key insight**: Put critical instructions and the most-important retrieved chunk at the *edges* of the window, not the middle.

### 5. Context Rot — When the Window Poisons Itself
Stale tool results, abandoned plans, resolved errors, and superseded user instructions accumulate in long-running agents. The model dutifully attends to all of it, including the parts that no longer apply. Symptoms: agent re-tries already-failed tools, contradicts its own corrections, or follows a plan it abandoned 10 turns ago.

- **Analogy**: Email thread with 40 forwards. The actual decision is buried under quoted replies; new participants act on stale info.
- **Animation**: Multi-turn agent transcript with rot accumulating (highlighted red); a "garbage collection" pass removes resolved items, agent behavior corrects.
- **Key insight**: Compaction isn't just about token budget — it's about *signal-to-noise*. A smaller, cleaner context often beats a larger, noisier one.

## Code Walkthrough
Build a `ContextBudget` class (Python and Node.js) that:
1. Takes a system prompt, tool list, message history, retrieved chunks, and current turn
2. Reports per-layer token counts and total
3. Applies one of four strategies (`add_all`, `compress_history`, `retrieve_top_k`, `offload_to_subagent_stub`) when the total exceeds a target budget
4. Returns the assembled `messages` array ready for the Anthropic SDK

Annotated in 4 chunks: layer accounting, the budget check, strategy dispatch, final assembly. Each chunk has WHAT/WHY/GOTCHA. The GOTCHA on strategy dispatch covers the static-first ordering rule for caching.

## Hands-On Lab
**The Poisoned Transcript.** Learner is given a real 30-turn agent transcript (UCC research domain) where the agent starts strong but degrades — by turn 25 it's re-running failed searches, contradicting earlier corrections, and burning tokens. Total context is at 92% of window.

Tasks:
1. Run a diagnostic script that prints per-layer token breakdown and flags rot signals (duplicate tool calls, superseded instructions, resolved errors)
2. Fix it three different ways using three of the four levers:
   - **Compress**: Replace the first 15 turns with a summary, keep the last 10 verbatim
   - **Retrieve**: Switch tool results from "kept inline" to "stored, retrieved on reference"
   - **Offload**: Spawn a research subagent for the search-heavy middle, return only its final report
3. Re-run the same final user question against all three fixed versions; compare answer quality, token count, and latency

**Stretch goals**:
- Implement static-first reordering and measure cache hit rate change
- Add a position-effects test: move the critical instruction from middle to end, measure accuracy delta

## Quiz Focus (5 questions)
1. **Multiple choice**: Which is NOT one of the four context-engineering levers? (add / compress / retrieve / offload / *encrypt*)
2. **Code completion**: Given a `messages` array, reorder it so prompt caching can hit. (Static blocks before dynamic.)
3. **Scenario**: An agent works fine for 5 turns then degrades. Token usage is at 60%, well under the limit. What's the most likely cause? (Context rot — accumulated stale content lowers signal-to-noise even below the budget ceiling.)
4. **Multiple choice**: You have a 20-page reference doc the agent needs occasional facts from. Which lever fits best? (Retrieve — not add, since most facts won't be relevant per turn.)
5. **Conceptual**: Why does putting the most important instruction in the middle of a long context hurt accuracy? (Lost-in-the-middle — attention concentrates on the edges.)

## Forward References
- **M07 (MCP)**: Tool definitions are static context — covered as a caching opportunity here
- **M08 (Conversation Management)**: Operationalizes the *compress* lever for message history
- **M09–M10 (RAG)**: Operationalizes the *retrieve* lever
- **M11 (Multi-Layer Memory)**: Combines retrieve + offload across short/long-term stores
- **M14 (Multi-Agent Systems)**: Subagents as the *offload* lever
- **M22 (Cost Optimization)**: Prompt caching, justified here by the static/dynamic split
