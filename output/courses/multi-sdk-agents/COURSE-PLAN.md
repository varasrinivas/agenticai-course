# Course Plan — Building AI Agents Across the Big Three SDKs

**Working title:** *One Agent, Three SDKs — Building AI Agents with Anthropic, Google Gemini & OpenAI*

## Premise
Every module teaches **one agent concept** and builds **the same agent three ways** — side by side in the Anthropic (Claude), Google (Gemini), and OpenAI SDKs — so the learner sees exactly where the three providers agree, where they differ, and why. A learner who knows one SDK can read across to the other two in a glance.

## Running example (threads through all modules)
**"Acme Support"** — an e-commerce customer-support agent for a fictional online store.
- Tools it grows over the course: `get_order_status`, `search_products`, `process_refund`, `search_help_docs` (RAG).
- Module by module it gains: tool use → structured output → multi-tool orchestration → memory → retrieval grounding → a triage/specialist multi-agent team → production hardening.

## Code-presentation convention
Each code example uses a **6-tab code block**, color-coded by provider:

| Tab | Provider | Language |
|---|---|---|
| Anthropic · Py | Claude (`anthropic`) | Python |
| Anthropic · JS | Claude (`@anthropic-ai/sdk`) | Node.js |
| Google · Py | Gemini (`google-genai`) | Python |
| Google · JS | Gemini (`@google/genai`) | Node.js |
| OpenAI · Py | GPT (`openai`) | Python |
| OpenAI · JS | GPT (`openai`) | Node.js |

Provider signature colors:
- **Anthropic** — `#D97757` (terracotta) / accent gold
- **Google Gemini** — `#4285F4` (blue)
- **OpenAI** — `#10A37F` (teal-green)

Each module ends with a **"Three ways, one idea"** comparison table (the same concept mapped across the three SDKs' vocabulary) plus a **"Why the differences?"** callout.

## Module map (8 focused modules, M00–M07)

| # | Title | Core concept | Acme Support milestone |
|---|---|---|---|
| **M00** | Setup & Three Clients | Install 3 SDKs, keys, model IDs, first `generate` call each | "Hello, Acme" one-shot reply |
| **M01** | The Agent Loop & Tool Use | Function calling + the tool-use loop | `get_order_status` tool |
| **M02** | Structured Output | Schema-constrained JSON out of each SDK | Return a typed `OrderStatus` object |
| **M03** | Multi-Tool Orchestration | Many tools, parallel calls, loop-until-done | Add `search_products` + `process_refund` |
| **M04** | Memory & Conversation | Multi-turn state: stateless history vs. chat sessions vs. stored state | Remembers the customer across turns |
| **M05** | RAG / Retrieval Grounding | Embeddings + retrieval to ground answers in help docs | `search_help_docs` over a KB |
| **M06** | Multi-Agent Systems | Triage → specialist handoff; each provider's agent framework | Triage agent routes to Orders/Refunds specialists |
| **M07** | Production | Streaming, errors/retries, cost, and each provider's agent framework as the graduation | Hardened, deployable Acme Support |

## SDK framework note (surfaced in M06–M07)
- **Anthropic** — raw Messages API + the **Claude Agent SDK** / tool runner; subagents.
- **Google** — the **google-genai** SDK + the **Agent Development Kit (ADK)** for multi-agent.
- **OpenAI** — Chat Completions / **Responses API** + the **OpenAI Agents SDK** (`openai-agents` / `@openai/agents`) for handoffs.

## Accuracy policy
All model IDs, package names, and function-calling shapes are verified against current official docs before writing (see per-module fact sheets). Every code example is complete and runnable, with error handling — never pseudocode.

## Build status
- [x] Scaffold + plan
- [x] Index / landing page
- [x] M00 — Setup & Three Clients
- [x] M01 — The Agent Loop & Tool Use
- [x] M02 — Structured Output
- [x] M03 — Multi-Tool Orchestration
- [x] M04 — Memory & Conversation
- [x] M05 — RAG / Retrieval Grounding
- [x] M06 — Multi-Agent Systems
- [x] M07 — Production

**COMPLETE ✅** — all 8 modules + index built, browser-verified, and consistent.
Every SDK shape (models, packages, function calling, structured output,
embeddings, multi-agent frameworks, streaming/errors/usage) was verified
against current official docs before writing.
