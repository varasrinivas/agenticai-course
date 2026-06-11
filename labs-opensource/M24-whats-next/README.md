# M24: What's Next — The Frontier (Reading Module)

> M24 is a code-free outlook module — there is no lab to build. This checklist turns it into an active reading session instead.

## Read the Module

`output/courses/opensource/M24-whats-next-frontier.html`

## Reading Checklist

Work through the module and check these off:

- [ ] **The open-weights frontier**: can you name the current leading open model families and what distinguishes them (size, license, context length)?
- [ ] **Local inference trends**: quantization formats (GGUF, Q4/Q8), speculative decoding, and why consumer hardware keeps closing the gap
- [ ] **Agent standards**: where MCP and OpenAI-compatible tool calling are converging, and what that means for the portability patterns you used all course
- [ ] **Multimodality on local hardware**: what vision/audio models run under Ollama today, and what their realistic limits are
- [ ] **The skills audit**: list the 5 components you built in this course that survive ANY model swap (the loop, guardrails, tracing, evals, caching) versus the parts that are model-specific (prompts, thresholds)

## Closing Exercises (no new code — consolidation)

1. **The swap test**: take your M12 ReAct agent and run it against a different model (`ollama pull llama3.1:8b`, change one string). Write down everything that broke. (Spoiler: usually just prompt-sensitivity and tool-call reliability — your architecture survives.)
2. **Re-run the M22 benchmark** with the newest model that fits your hardware. Has your "smallest model that clears the bar" answer changed since you started the course?
3. **Portfolio check**: you now have ~20 runnable labs. Pick the three that best demonstrate production thinking (suggestions: M16 guardrails, M19 tracing, CAPSTONE-C3) and polish them for your portfolio repo.

## Where to Go From Here

- The **Claude track** (`../labs/`) — the same curriculum against hosted frontier models, including the Agent SDK tiers
- **CAPSTONE-C3** (`../CAPSTONE-C3-entity-resolution/`) — if you haven't done it yet, it's the course's integration exam
- The course index: `output/courses/opensource/index.html`
