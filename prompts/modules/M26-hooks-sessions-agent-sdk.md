# M26: Build with the Agent SDK — Hooks, Sessions & Declarative Agents

**Track**: 9 — Cert Prep | **Position**: 26 of 30 | **Level**: Advanced
**Prerequisites**: M05, M12, M15B, M25
**Estimated Time**: 90-120 minutes

## 6 Sections

### Section 1: Raw Loop vs Agent SDK
Comparison table: 60 lines manual vs 15 lines SDK. When to use which.

### Section 2: Build UCC Agent with SDK (Steps 1-4)
Step 1: Setup. Step 2: @agent.tool decorators. Step 3: Run in 5 lines. Step 4: Side-by-side comparison.

### Section 3: Hooks (Steps 5-7)
Step 5: PreToolUse logging. Step 6: PreToolUse blocking broad queries. Step 7: PostToolUse PII redaction.

### Section 4: Sessions (Step 8)
session.send() for multi-turn. session.fork() for what-if branches.

### Section 5: Production Agent (Step 9)
SDK + hooks + sessions + ML model tool combined.

### Section 6: Decision Guide
| Factor | Use Raw Loop | Use Agent SDK |
| Custom loop control | Yes | No |
| Standard patterns | Overkill | Yes |
| Guardrails via hooks | Write manually | Built-in |
| Production speed | Slower | Faster |

### Debugging: Hooks + Anthropic Console Web UI + Langfuse
- console.anthropic.com > Logs: inspect every API call
- Hooks as modular debug probes (add/remove cleanly)
- Langfuse trace waterfall for timing

## Animations
1. Raw vs SDK comparison. 2. Hook lifecycle. 3. Session forking tree. 4. Production agent stack.
