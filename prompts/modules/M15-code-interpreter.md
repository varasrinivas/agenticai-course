# M15: Code Interpreter & Sandbox Execution

**Track**: 4 — Agent Architectures | **Position**: 15 of 30 | **Level**: Intermediate → Advanced
**Prerequisites**: M05, M12
**Estimated Time**: 60-75 minutes
**Track Color**: var(--track-architecture) / #F97316

## Concepts
- Why agents need to run code (the "calculation gap" — LLMs can't do math reliably)
- Sandboxed execution: Docker, E2B, Pyodide (animated comparison)
- Security model: path traversal, resource exhaustion, network access (animated attack vectors)
- Implementing a code execution tool for Claude
- Result parsing and error recovery
- Visual: Animated sandbox showing code execution in isolation

## Hands-On Lab
Build an agent that writes and executes Python to analyze UCC filing data: count filings by state, calculate average collateral value, generate a bar chart. All execution in a Docker sandbox.

## Quiz Focus (5 questions)
1. Why can't Claude just do math in its head? (LLMs predict tokens, not compute arithmetic)
2. What does "sandboxed" mean? (isolated environment — can't access host filesystem or network)
3. Is a sandbox automatically safe? (no — resource limits, timeout, no network needed too)
4. What if the generated code has a syntax error? (catch error, send it back to Claude, retry)
5. When should you use code execution vs a dedicated tool? (code for dynamic computation, dedicated tool for fixed operations)
