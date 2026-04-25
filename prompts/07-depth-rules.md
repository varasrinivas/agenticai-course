# Content Depth Rules — Apply to Every Module

These rules ensure modules TEACH rather than just PRESENT. Every module generation and review must check against these.

## RULE 1: Unpack Every Analogy (minimum 3 sentences)
BAD: "MCP is like USB-C for AI."
GOOD: Walk through 3 steps:
  - BEFORE state: "Before USB-C, your iPhone needed Lightning, your Android needed Micro-USB, your laptop needed a barrel jack..."
  - PAIN: "This meant you carried 3 cables, and every new device was another cable to buy..."
  - MAPPING: "MCP works the same way — before MCP, Claude needed a custom integration for Slack, another for GitHub, another for your database. MCP is the one universal plug."

## RULE 2: Teach Technical Definitions, Don't Dictate
BAD: "MCP uses JSON-RPC 2.0 over stdio or HTTP+SSE transports."
GOOD: Explain what each term MEANS and WHY it was chosen:
  "When Claude talks to your MCP server, they exchange small JSON messages — the client says 'run this tool with these inputs' and the server sends back the result. That pattern is called JSON-RPC — just named method calls with parameters, sent as JSON."
  Then explain each transport option and WHEN to use it.
  Define every sub-term on first use. Never assume the learner knows jargon.

## RULE 3: Annotate Code in Chunks (never dump 50+ lines unexplained)
BAD: One-line intro → 60-line code block
GOOD: Break code into 3-5 logical chunks. Before each chunk:
  - WHAT: "This section sets up path security." (1 sentence)
  - WHY: "Without this, an AI model could read any file on your machine." (1 sentence)
  - GOTCHA: "Common mistake: forgetting to resolve symlinks — a path like ../../etc/passwd bypasses naive checks." (if applicable)
Show the chunk. Then explain the next chunk.

After the complete code block, add a "What Just Happened?" checkpoint:
  "You just created a server with 3 tools. When Claude connects, it sees these tools in its menu and can call them. The server runs as a subprocess — no network, no auth, just stdin/stdout."

## RULE 4: Quantify "Why It Matters"
BAD: "MCP transforms N×M into N+M."
GOOD: "Your team uses Claude and Gemini. You have 4 tools: Jira, PostgreSQL, deploy pipeline, docs. Without MCP: 2 × 4 = 8 custom integrations. With MCP: 2 + 4 = 6. But the real win is maintenance — when Jira's API changes, update ONE MCP server, both AI models get the fix."

## RULE 5: Add Conceptual Bridges Between Sections
Between "What is X" and "Build X", add a thinking bridge:
  "Now you understand WHAT MCP is. Before writing code, ask yourself: What data does my project have that an AI would benefit from? For the UCC pipeline, that's BigQuery queries and risk profiles. For your project, it might be a database or an API. The MCP server bridges your data and the AI model."

## RULE 6: Explain Decisions, Not Just Syntax
BAD: "@server.tool() decorator registers the function as a tool."
GOOD: "The @server.tool() decorator is the key line — it tells MCP 'this Python function should be exposed as a tool that AI models can call.' Without it, the function exists but is invisible to Claude. The decorator also auto-generates the tool's JSON Schema from your function signature — so the `path: str` parameter becomes `{type: 'string'}` in the schema automatically."

## RULE 7: Connect Every Section to the UCC Domain
Don't just explain abstract concepts. Show how they apply:
  "In the UCC pipeline, you'd create MCP tools for: searching filings by debtor name, checking entity risk profiles in BigQuery, and looking up filing amendment history. Each tool maps to a Gold-layer query."

## RULE 8: Break Dense Sentences (max 2 technical concepts per sentence)
BAD: "Documents are loaded, chunked into segments, embedded into vectors, stored in a vector database, and retrieved at query time to augment the prompt sent to Claude."
GOOD: "RAG works in two phases. First, the SETUP phase (you do this once): take your documents, break them into small pieces, and convert each piece into a number array. Save those arrays in a special database. Second, the QUERY phase (this happens every time a user asks a question): search that database for the pieces most related to the question, paste them into the prompt, and let Claude answer. That's it — search, then generate."

If a sentence has 3+ technical terms or concepts, split it. Use conversational transitions:
  - "First... Second... Finally..."
  - "Here's what happens step by step:"
  - "That's it — just [simple summary]."
  - "In other words, [restate in simpler terms]."

## RULE 9: Land Analogies With Concrete Artifacts
After every analogy, show what the concept LOOKS LIKE in practice. Bridge from metaphor to reality:
  - After embeddings analogy → show an actual embedding: [0.023, -0.841, 0.129, ...1533 more floats...]
  - After chunking analogy → show what a chunk object looks like: {text: "The debtor...", source: "filing_NY_2024.txt", chunk_index: 3}
  - After vector DB analogy → show a "row": vector + original text + metadata side by side
  - After MCP analogy → show the actual JSON-RPC message that goes over the wire

The learner should be able to say: "Oh, THAT'S what it looks like in real code."

## RULE 10: Expand Thin Sections (minimum 3 paragraphs per new concept)
If a concept appears for the FIRST TIME in the course (vector databases, embeddings, hooks, MCP, ReAct), it needs at least 3 paragraphs:
  1. What it IS (in plain English)
  2. How it WORKS internally (one level deeper — what's actually happening under the hood)
  3. How it DIFFERS from what the learner already knows (contrast with familiar concepts)

BAD: "Vector databases store vectors and support ANN search. Options: ChromaDB, Pinecone, pgvector." (1 paragraph, 2 sentences)
GOOD: Paragraph 1 explains what's stored (vector + text + metadata). Paragraph 2 explains how search works (embed query → find nearest vectors → return text). Paragraph 3 contrasts with SQL: "In PostgreSQL you'd write SELECT * WHERE debtor_name = 'Acme' — exact match. In a vector DB, you'd say 'find me everything semantically similar to Acme Corporation' and it would also find 'ACME CORP', 'Acme Corp Inc', and related entities."

## RULE 11: Conversational Code Annotations (teach, don't list)
Code annotations should sound like a teacher thinking through the problem, not bullet points.

BAD: "WHAT: We load all .md and .txt files. WHY: Embedding models need input. GOTCHA: Handle encoding errors."

GOOD: "Let's start by getting our documents into the system. The `load_documents` function is straightforward — it reads every markdown and text file from a folder and returns them as a list. Nothing clever here, just file I/O with proper error handling (we skip files with encoding issues rather than crashing the whole pipeline).

The interesting part is `chunk_text`. Here's the dilemma: embedding models work best with short text — typically under 512 tokens — but our documents might be thousands of words. We COULD just chop the text every 500 characters, but that might cut a sentence in half. So instead, the function tries to find a natural break point — a paragraph boundary, a period, or at worst a space — before making the cut. This small detail makes a real difference in retrieval quality."

Notice the difference: the second version tells a STORY. It has tension ("here's the dilemma"), reasoning ("we COULD... but"), and payoff ("this small detail makes a real difference").

## RULE 12: Add Common Misconceptions for Major Concepts
For every major NEW concept introduced in a module (RAG, embeddings, MCP, ReAct, multi-agent, hooks, vector DBs), add a "Common Misconceptions" callout box with 3-5 wrong mental models and corrections.

Format:
```html
<div class="callout-warning">
  <span class="box-label">⚠️ Common Misconceptions</span>
  <p><strong>"RAG is just fine-tuning, right?"</strong> — No. Fine-tuning changes the model's weights ($5K-$50K, takes weeks). RAG doesn't touch the model at all — it just adds relevant text to the prompt. Think of it as giving Claude a cheat sheet, not retraining Claude.</p>
  <p><strong>"Bigger chunks = better results?"</strong> — Usually the opposite. A 2000-word chunk that contains one relevant sentence dilutes the signal. The retriever found the right chunk, but Claude has to wade through 1999 irrelevant words to find the answer.</p>
</div>
```

Why this matters: beginners form mental models FAST, and wrong models are harder to fix later. Proactively correcting misconceptions prevents hours of debugging from wrong assumptions.

## RULE 13: Hands-On Labs Must Be Step-by-Step Executable
Every module's hands-on exercise must follow this structure:

### Lab Header
- **What You'll Build**: One sentence describing the final artifact ("A RAG pipeline that answers questions about UCC filing documents")
- **Time Estimate**: Realistic time ("30-45 minutes")
- **Prerequisites**: What must be installed and configured before starting
- **Files You'll Create**: List every file with its purpose

### Environment Setup Block
A single copy-pasteable block that installs everything:
```
mkdir project-name && cd project-name
python -m venv venv && source venv/bin/activate   # or: venv\Scripts\activate on Windows
pip install anthropic chromadb pydantic
export ANTHROPIC_API_KEY=your-key-here             # or: set ANTHROPIC_API_KEY=your-key-here on Windows
```

### Numbered Steps (every step must have ALL of these):
1. **Step Title** — what you're doing ("Step 1: Create the document loader")
2. **What & Why** — 2-3 sentences explaining what this step does and why it matters
3. **Create/Edit Instruction** — explicit: "Create a new file called `loader.py`" or "Add the following to `loader.py` after line 20"
4. **Complete Code Block** — the FULL code for this step (not a diff, not a snippet — the complete file or function)
5. **Run Command** — exactly what to type in the terminal to test this step
6. **Expected Output** — what the student should see (exact terminal output, formatted in an output block)
7. **Checkpoint** — a green callout box: "✅ If you see [expected output], Step 1 is working. If not, check [common issues]."
8. **Troubleshooting** — 2-3 common errors with fixes:
   - "If you see `ModuleNotFoundError: No module named 'chromadb'` → run `pip install chromadb`"
   - "If you see `AuthenticationError` → check your ANTHROPIC_API_KEY is set"

### Step Dependencies Must Be Explicit
If Step 3 uses output from Step 1, say so:
  "This step uses the `chunks` list created in Step 1. If you're starting fresh, run Steps 1-2 first."

### Final Verification
After all steps, a "Verify Everything Works" section:
- A single command that runs the complete pipeline end-to-end
- Expected final output
- "🎉 Congratulations" checkpoint confirming completion

BAD lab instruction:
  "Build a RAG pipeline. Load documents, chunk them, embed them in ChromaDB, and query with Claude."

GOOD lab instruction:
  "Step 1: Create the document loader
   Create a new file called `loader.py`:
   [complete code]
   Test it: `python -c "from loader import load_documents; print(load_documents('./docs'))"`
   Expected output: `[{'content': '...', 'source': 'filing_guide.md'}]`
   ✅ Checkpoint: You should see a list of document dictionaries. Each has 'content' and 'source' keys."

## RULE 14: Capstone Projects Must Include Full Lab Packets
Capstone projects need EVERYTHING a student needs to build the project independently:

### Project Packet Contents:
1. **Project Brief** — business context, what you're building, who it's for (2-3 paragraphs)
2. **Architecture Diagram** — animated SVG showing all components and data flow
3. **File Structure** — complete directory tree showing every file to create:
   ```
   capstone-3-research-agent/
   ├── agent.py              # Main agent loop
   ├── tools.py              # Tool definitions
   ├── mock_data.py          # Mock API responses
   ├── test_agent.py         # Test cases
   ├── requirements.txt      # Dependencies
   └── README.md             # Setup instructions
   ```
4. **Mock Data File** — complete, realistic mock data (not "insert your data here"):
   - For UCC domain: 10-15 mock filings with realistic debtor names, secured parties, collateral descriptions, state codes
   - For Healthcare: 5-10 mock pre-auth requests with CPT codes, ICD-10 codes, payer responses
   - For B2B: 5-10 mock POs with line items, shipping status, carrier tracking
5. **Step-by-Step Build Guide** — follows Rule 13 exactly, numbered steps with code/run/output/checkpoint
6. **Test Cases** — at least 5 test scenarios the student can run:
   - 3 happy path (normal operation)
   - 1 edge case (missing data, ambiguous input)
   - 1 error case (API failure, invalid input)
   Each test case: input → expected behavior → expected output
7. **"Going Further" Extensions** — 3-5 optional stretch goals marked as OPTIONAL:
   - "Add a second tool for..."
   - "Implement caching to reduce API calls..."
   - "Add error retry logic with exponential backoff..."

### Capstone Difficulty Calibration:
- ★☆☆☆☆: 3-5 steps, ~30 min, single tool, linear flow
- ★★☆☆☆: 5-8 steps, ~60 min, RAG pipeline, multiple files
- ★★★☆☆: 8-12 steps, ~90 min, multi-tool agent with reasoning loop
- ★★★★☆: 12-18 steps, ~2-3 hours, multi-agent pipeline with HITL
- ★★★★★: 18-25 steps, ~4-6 hours, full production system with guardrails + observability

## APPLICATION CHECKLIST (run mentally for every section)
- [ ] Would a beginner understand this without Googling any term?
- [ ] Could the learner explain this concept to a colleague after reading?
- [ ] Is every code block explained in chunks, not just labeled?
- [ ] Are numbers/examples concrete, not abstract?
- [ ] Does the section connect to the previous and next section logically?
- [ ] Are dense sentences broken up? (max 2 technical concepts per sentence)
- [ ] Does every analogy land with a concrete "what it looks like" artifact?
- [ ] Are new concepts given at least 3 paragraphs of explanation?
- [ ] Do code annotations sound like a teacher talking, not a manual listing?
- [ ] Are common misconceptions called out for major new concepts?
- [ ] Does the hands-on lab have numbered steps with code/run/output/checkpoint for EVERY step?
- [ ] Can a student execute the lab from scratch following ONLY the instructions given?
