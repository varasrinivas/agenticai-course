# Module Content Reference

This file contains the detailed concept list for every module. Used by `/generate-all-briefs` to create individual module brief files.

---

## MODULE 3: [M03] Prompts — Programming in Natural Language
Track: 1 — Foundations | Position: 3 of 30 | Level: Beginner
Prerequisites: M01, M02
Estimated Time: 50-60 minutes
Track Color: var(--track-foundations) / #6366F1

Concepts:
- Anatomy of a prompt: system, user, assistant roles (visual message flow)
- Prompt engineering patterns:
  - Zero-shot, few-shot, chain-of-thought (animated comparison)
  - Role prompting, structured output (XML/JSON), delimiters
- The "prompt → completion" loop animated end-to-end
- System prompts as "personality programming" — interactive builder
- Hands-on: Build a multi-turn conversation manager
- Visual: Animated message stack showing how Claude sees the conversation

---

## MODULE 3B: [M03B] Context Engineering — Curating What the Model Sees
Track: 1 — Foundations | Position: After M03, before M04 | Level: Beginner → Intermediate
Prerequisites: M01, M02, M03
Estimated Time: 50-60 minutes
Track Color: var(--track-foundations) / #6366F1

Concepts:
- Prompt engineering vs. context engineering — writing the message vs. curating everything the model sees
- The "what does the model actually see?" inventory: system + tools + history + retrieved + tool results + current turn (animated stacked layers with token meter)
- The four levers: add, compress, retrieve, offload — the organizing frame for Track 3
- Static vs. dynamic context — why ordering matters for prompt caching (sets up M22)
- Position effects — lost-in-the-middle, putting critical content at the edges
- Context rot — stale tool results, superseded instructions, resolved errors poisoning long-running agents
- Hands-on: The Poisoned Transcript lab — diagnose a 30-turn rotting agent, fix it three ways (compress / retrieve / offload), compare answer quality + tokens + latency
- Visual: Side-by-side naive vs. engineered context solving the same task with token counts and quality scores

---

## MODULE 4: [M04] Structured Output & Parsing
Track: 1 — Foundations | Position: 4 of 30 | Level: Beginner → Intermediate
Prerequisites: M01-M03
Estimated Time: 50-60 minutes
Track Color: var(--track-foundations) / #6366F1

Concepts:
- Why agents need structured responses (JSON, XML, tool-use format)
- Claude's native tool use / function calling — how it works under the hood
  - Animated: The "restaurant menu" analogy — tools as menu items Claude picks from
- JSON mode, stop sequences, and output validation
- Pydantic/Zod schemas for response validation
- Error recovery: What happens when parsing fails?
- Hands-on: Build a structured data extraction pipeline
- Visual: Animated flow from natural language → structured JSON → application state

---

## MODULE 6: [M06] Multi-Tool Orchestration
Track: 2 — Tool Use | Position: 6 of 30 | Level: Intermediate
Prerequisites: M05
Estimated Time: 60-75 minutes
Track Color: var(--track-tooluse) / #8B5CF6

Concepts:
- Parallel tool calls — when and why
- Sequential tool chains — output of tool A feeds tool B
- Tool selection strategies: how Claude picks the right tool
  - Interactive: "What tool would YOU pick?" quiz matching Claude's reasoning
- Dynamic tool registration — adding/removing tools at runtime
- Hands-on: Build a research assistant that searches, fetches, summarizes
- Visual: Animated DAG (Directed Acyclic Graph) showing tool execution order

---

## MODULE 7: [M07] MCP — Model Context Protocol
Track: 2 — Tool Use | Position: 7 of 30 | Level: Intermediate
Prerequisites: M05, M06
Estimated Time: 60-75 minutes
Track Color: var(--track-tooluse) / #8B5CF6

Concepts:
- What is MCP? The "USB-C for AI" analogy (animated)
- MCP architecture: Client ↔ Server ↔ Resources/Tools/Prompts
  - Visual: Animated protocol handshake sequence
- Building your first MCP server (Python + Node.js)
- Connecting Claude Desktop / Claude Code to your MCP server
- Resources vs. Tools vs. Prompts — when to use each
- Hands-on: Build a filesystem MCP server + a database MCP server
- Visual: Animated MCP message flow with protocol frames highlighted

---

## MODULE 8: [M08] Conversation Management
Track: 3 — Memory & Context | Position: 8 of 30 | Level: Intermediate
Prerequisites: M01-M04
Estimated Time: 50-60 minutes
Track Color: var(--track-memory) / #06B6D4

Concepts:
- The stateless reality: Claude has no memory between API calls
- Conversation history management patterns
  - Full history, sliding window, summarization (animated comparison)
- Token budget allocation: system prompt + history + user message + response
  - Interactive: Token budget calculator with draggable allocation sliders
- Message pruning strategies — what to keep, what to drop
- Hands-on: Build a conversation manager with automatic summarization
- Visual: Animated "memory palace" showing conversation state management

---

## MODULE 9: [M09] RAG — Retrieval-Augmented Generation
Track: 3 — Memory & Context | Position: 9 of 30 | Level: Intermediate
Prerequisites: M01-M04, M08
Estimated Time: 75-90 minutes
Track Color: var(--track-memory) / #06B6D4

Concepts:
- The knowledge problem: Claude's training cutoff and domain gaps
- What is RAG? (animated end-to-end pipeline visualization)
  - Document loading → Chunking → Embedding → Storage → Retrieval → Generation
- Embeddings explained from scratch:
  - "Words as coordinates in meaning-space" (interactive 3D visualization)
  - Cosine similarity — animated vector comparison
- Chunking strategies: fixed-size, semantic, recursive (visual comparison)
- Vector databases: What they are, how they work (animated index lookup)
  - Practical: ChromaDB / Pinecone / pgvector comparison
- The RAG pipeline step-by-step with animated data flow
- Hands-on: Build a "Chat with your docs" RAG system
- Visual: Animated embedding space with query vector finding nearest neighbors

---

## MODULE 10: [M10] Advanced RAG Patterns
Track: 3 — Memory & Context | Position: 10 of 30 | Level: Advanced
Prerequisites: M09
Estimated Time: 60-75 minutes
Track Color: var(--track-memory) / #06B6D4

Concepts:
- Naive RAG vs. Advanced RAG (visual comparison)
- Hybrid search: keyword (BM25) + semantic (vector) — animated fusion
- Re-ranking: Why retrieval order matters (animated re-ranking pipeline)
- Query transformation: HyDE, multi-query, step-back prompting
  - Visual: Animated query expansion showing how one question becomes many
- Contextual compression — trimming retrieved chunks
- Evaluation: How to measure RAG quality (precision, recall, faithfulness)
- Hands-on: Upgrade your RAG system with hybrid search + re-ranking
- Visual: Side-by-side comparison of naive vs. advanced RAG answering the same question

---

## MODULE 11: [M11] Multi-Layer Memory Architecture
Track: 3 — Memory & Context | Position: 11 of 30 | Level: Advanced
Prerequisites: M08, M09
Estimated Time: 60-75 minutes
Track Color: var(--track-memory) / #06B6D4

Concepts:
- Why one memory type isn't enough (animated "human memory" analogy)
- Tier 1: Working Memory — scratchpad for current task state
- Tier 2: Episodic Memory — vector DB of past interactions
- Tier 3: Procedural Memory — skill library of learned tool sequences
- Summarization pipeline: compressing long conversations
- Memory compaction and cross-session persistence
- Hands-on: Build a 3-tier memory system with persistence
- Visual: Animated brain diagram showing memory tiers activating during a task

---

## MODULE 12: [M12] The ReAct Pattern
Track: 4 — Agent Architectures | Position: 12 of 30 | Level: Intermediate
Prerequisites: M05, M06
Estimated Time: 60-75 minutes
Track Color: var(--track-architecture) / #F97316

Concepts:
- What is an agent? (animated comparison: chatbot vs. agent)
- The ReAct loop: Reason → Act → Observe → Repeat
  - Animated step-by-step showing the thinking/action cycle
- Implementing ReAct with Claude's tool use
- Thought traces: Why making Claude "think out loud" improves results
- Stop conditions: When should the agent stop looping?
- Hands-on: Build a ReAct research agent that reasons through multi-step questions
- Visual: Animated ReAct loop with thought bubbles and action arrows

---

## MODULE 13: [M13] Planning & Task Decomposition
Track: 4 — Agent Architectures | Position: 13 of 30 | Level: Intermediate → Advanced
Prerequisites: M12
Estimated Time: 60-75 minutes
Track Color: var(--track-architecture) / #F97316

Concepts:
- Why complex tasks need planning (the "IKEA furniture" analogy)
- Intent classification: Understanding what the user actually wants
  - Animated decision tree showing classification flow
- Task decomposition: Breaking big tasks into sub-tasks
  - Visual: Animated tree decomposition of a complex request
- DAG (Directed Acyclic Graph) execution:
  - What is a DAG? (animated graph construction)
  - Parallel vs. sequential execution paths
  - Dependency resolution
- Dynamic tool discovery: Finding the right tools at runtime
- Hands-on: Build a planning agent that decomposes and executes multi-step tasks
- Visual: Animated DAG builder showing task dependencies and execution order

---

## MODULE 14: [M14] Multi-Agent Systems
Track: 4 — Agent Architectures | Position: 14 of 30 | Level: Advanced
Prerequisites: M12, M13
Estimated Time: 75-90 minutes
Track Color: var(--track-architecture) / #F97316

Concepts:
- When one agent isn't enough — the "team of specialists" model
- Architecture patterns:
  - Supervisor/worker (animated org chart)
  - Peer-to-peer (animated message passing)
  - Pipeline (animated assembly line)
- Agent communication protocols — message formats and handoffs
- Shared state vs. message passing (animated comparison)
- Conflict resolution: What if agents disagree?
- Hands-on: Build a content creation pipeline (researcher → writer → editor → reviewer)
- Visual: Animated multi-agent collaboration with message flow visualization

---

## MODULE 15: [M15] Code Interpreter & Sandbox Execution
Track: 4 — Agent Architectures | Position: 15 of 30 | Level: Intermediate → Advanced
Prerequisites: M05, M12
Estimated Time: 60-75 minutes
Track Color: var(--track-architecture) / #F97316

Concepts:
- Why agents need to run code (the "calculation gap")
- Sandboxed execution: Docker, E2B, Pyodide (animated comparison)
- Security model: What can go wrong? (animated attack vectors)
- Implementing a code execution tool for Claude
- Result parsing and error recovery
- Hands-on: Build an agent that writes and executes Python to solve data analysis tasks
- Visual: Animated sandbox showing code execution in an isolated environment

---

## MODULE 16: [M16] Input Guardrails
Track: 5 — Guardrails & Safety | Position: 16 of 30 | Level: Intermediate
Prerequisites: M05, M12
Estimated Time: 60-75 minutes
Track Color: var(--track-guardrails) / #EF4444

Concepts:
- Why guardrails matter (animated "guardrail failure" scenarios)
- PII detection and redaction (interactive — paste text, see PII highlighted)
- Prompt injection attacks explained:
  - What they are (animated attack flow)
  - Direct injection, indirect injection, jailbreaks
  - Detection and prevention strategies
- Schema validation: Ensuring inputs match expected formats
- Rate limiting and abuse prevention
- Hands-on: Build an input validation pipeline with PII detection + injection defense
- Visual: Animated "firewall" showing inputs being screened

---

## MODULE 17: [M17] Output Guardrails & Human-in-the-Loop
Track: 5 — Guardrails & Safety | Position: 17 of 30 | Level: Intermediate → Advanced
Prerequisites: M16
Estimated Time: 60-75 minutes
Track Color: var(--track-guardrails) / #EF4444

Concepts:
- Output validation: Hallucination detection, toxicity filtering, format checks
- Cost controls: Budget limits, token caps, execution time limits
  - Interactive: Cost calculator showing how agent loops can explode
- Human-in-the-Loop (HITL) patterns:
  - Approval gates — pause for human review (animated workflow)
  - Modification gates — human can edit before proceeding
  - Escalation gates — agent recognizes its limits
- Circuit breaker pattern: Automatic shutdown on repeated failures
  - Animated: Failure count → threshold → fallback route
- Hands-on: Add guardrails + HITL approval to your planning agent
- Visual: Animated pipeline with guardrail checkpoints lighting up green/red

---

## MODULE 18: [M18] Evaluation & Testing
Track: 5 — Guardrails & Safety | Position: 18 of 30 | Level: Intermediate → Advanced
Prerequisites: M12, M16, M17
Estimated Time: 60-75 minutes
Track Color: var(--track-guardrails) / #EF4444

Concepts:
- Why agent testing is different from software testing
- Evaluation frameworks:
  - Task completion rate, tool accuracy, response quality
  - Automated evaluation with Claude-as-judge
- A/B testing for agents — comparing prompts, tools, strategies
- Regression testing: Ensuring changes don't break existing behavior
- Evaluation datasets: Building and maintaining test suites
- Hands-on: Build an eval harness that scores your agent on 50 test cases
- Visual: Animated dashboard showing eval metrics across agent versions

---

## MODULE 19: [M19] Tracing & Logging
Track: 6 — Observability | Position: 19 of 30 | Level: Intermediate
Prerequisites: M05, M12
Estimated Time: 50-60 minutes
Track Color: var(--track-observability) / #22C55E

Concepts:
- Why observability matters for agents (animated "debugging blind" scenario)
- Agent traces: What they are, why every call needs one
  - Visual: Animated trace waterfall (LLM call → tool call → retrieval → response)
- Spans: Nesting and timing of sub-operations
- Structured logging: What to log, what NOT to log (PII!)
- Tools: LangSmith, Arize, Langfuse, OpenTelemetry (comparison matrix)
- Hands-on: Instrument your agent with full tracing using Langfuse
- Visual: Animated trace explorer showing a real agent execution

---

## MODULE 20: [M20] Monitoring & Continuous Improvement
Track: 6 — Observability | Position: 20 of 30 | Level: Intermediate → Advanced
Prerequisites: M19
Estimated Time: 50-60 minutes
Track Color: var(--track-observability) / #22C55E

Concepts:
- Production monitoring dashboards
  - Latency tracking, token usage, success/failure rates
  - Drift detection: When agent behavior changes over time
- Alerting: What warrants a page vs. a ticket?
- Feedback loops: Using production data to improve the agent
- A/B testing in production — canary deployments for agents
- Hands-on: Build a monitoring dashboard for your agent
- Visual: Animated dashboard with live metrics updating

---

## MODULE 21: [M21] API Design & Deployment
Track: 7 — Production Deployment | Position: 21 of 30 | Level: Intermediate → Advanced
Prerequisites: M12, M16-M17, M19
Estimated Time: 60-75 minutes
Track Color: var(--track-deployment) / #3B82F6

Concepts:
- Designing the agent API: REST, WebSocket, Server-Sent Events
  - Animated: Streaming vs. polling — why streaming matters for agents
- Containerization: Docker packaging for your agent
- Cloud deployment: AWS Lambda, Google Cloud Run, Railway
- Scaling: Concurrent requests, queue-based processing
- Hands-on: Deploy your agent as a production API with streaming responses
- Visual: Animated deployment pipeline from code → container → cloud → user

---

## MODULE 22: [M22] Cost Optimization
Track: 7 — Production Deployment | Position: 22 of 30 | Level: Intermediate → Advanced
Prerequisites: M02, M12, M21
Estimated Time: 50-60 minutes
Track Color: var(--track-deployment) / #3B82F6

Concepts:
- The cost anatomy of an agent call (animated breakdown)
  - LLM tokens + tool executions + retrieval + compute
- Caching strategies: Prompt caching, response caching, embedding caching
- Model routing: Using cheaper models for simple tasks
- Token optimization: System prompt compression, output constraints
- Hands-on: Add caching + model routing to cut your agent's cost by 60%
- Visual: Animated cost waterfall showing where money goes and how to reduce it

---

## MODULE 24: [M24] What's Next — The Agent Frontier
Track: 8 — Capstones | Position: 24 of 30 | Level: All Levels
Prerequisites: None (standalone)
Estimated Time: 30-40 minutes
Track Color: var(--track-capstones) / #D4A843

Concepts:
- Emerging patterns: Agent-to-agent protocols, agent marketplaces
- Claude's evolving capabilities: Computer use, extended thinking
- Building responsibly: Ethics, alignment, and human oversight
- Resources: Communities, papers, open-source frameworks
- Your personal agent development roadmap

---

## MODULE 27B: [M27B] Cert Domain 5.6 Deep Dive — Provenance, Temporal, Stratified Review, Synthesis
Track: 9 — Cert Prep | Position: After M27, before exam | Level: Intermediate → Advanced
Prerequisites: M09, M11, M17, M18, M27
Estimated Time: 60-75 minutes
Track Color: var(--track-capstones) / #D4A843

Concepts:
- Information provenance — claim-source mappings, retraction propagation, structured output schema (not prose with parens)
- Temporal data handling — {value, valid_from, valid_to, source} fields, current vs as-of queries, missing-valid_to bug class
- Stratified sampling for human review — N from each confidence bucket, beats top-N and uniform
- Field-level confidence — beats document-level for high-stakes extraction, composes with stratified
- Synthesis output buckets — established / contested / single-source / temporal-warning, with paraphrase = agreement
- Hands-on: Healthcare Pre-Auth Synthesizer — 8-chunk fixture, 4 output buckets, stratified review queue, regression test for contested-claims trap
- Visual: Source retraction propagation, temporal timeline scrubber, stratified-vs-top-N sampling comparison, agreement detection

This module exists because Domain 5.6 has the most under-covered topics in the cert. Cert tips were added to M09, M11, M17, M18 but the cert tests these as a unified discipline. Take this module before any full timed practice exam.
