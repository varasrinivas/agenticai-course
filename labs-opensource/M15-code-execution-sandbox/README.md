# M15 Lab: Code Execution Sandbox

> Let the model WRITE code; let your code RUN it — in a child process with a timeout, never `exec()` in your own namespace. Then close the loop: feed errors back so the agent debugs itself.

## Prerequisites

- M12 complete

## Exercises

| Step | File | What You Build | Key Concept |
|------|------|---------------|-------------|
| 1 | `sandbox_executor.py` / `.js` | `SubprocessExecutor` | Temp file, `shell=False`, timeout → exit code 124, guaranteed cleanup |
| 2 | `code_agent.py` / `.js` | `CodeExecutionAgent` | Self-debugging loop: error text becomes the next prompt |

## Security Model (read before coding)

The subprocess approach is **dev-tier**: the child still has full filesystem access. The course covers three tiers — subprocess (this lab), Docker (`--network none --memory 256m --read-only`, the production answer), and E2B cloud sandboxes. Treat everything the model writes as untrusted input; the stretch goal upgrades to Docker.

## Step 1: SubprocessExecutor.run(code, timeout)

1. Write the code to a `NamedTemporaryFile(suffix=".py", delete=False)` — a temp file gives the child its own scope; `delete=False` so the child can open it after we close it
2. `subprocess.run([sys.executable, tmp_path], capture_output=True, text=True, timeout=timeout, shell=False)` — **`shell=False` is non-negotiable** (shell injection)
3. `TimeoutExpired` → return `ExecResult(stderr="Execution timed out...", exit_code=124)` (bash `timeout(1)` convention)
4. `finally: os.unlink(tmp_path)` — cleanup happens even on crash

`ExecResult.to_tool_content()` (provided) formats stdout/stderr/exit_code into the tool message the model reads.

## Step 2: The Self-Debugging Loop

`CodeExecutionAgent.run(user_request)`:
- System prompt (provided) tells the model: write COMPLETE code, import everything, PRINT the final answer, and **"if you receive an error, read it carefully, fix the code, and call execute_python again"** — that last sentence is the self-debugging mechanism; the loop just delivers the error
- Up to `max_retries + 1` rounds: call model (temperature 0.1 — determinism matters for code) → if no `tool_calls`, return the text answer → else execute each call, append results, loop
- After exhausting retries with a non-zero exit code, return the last error honestly

## Run It

```bash
python starter/sandbox_executor.py    # executor smoke tests (no LLM needed)
python starter/code_agent.py          # the full agent
```

The executor smoke test covers: a passing computation, a deliberate `NameError`, and an infinite loop (must time out at 124, not hang).

## Gotchas

- **Some Ollama builds silently ignore `tool_choice`** — always check `msg.tool_calls` rather than assuming.
- **Mistral-7B writes buggy code regularly. That's the point.** Watch attempt 2 fix attempt 1's NameError. If the model gives up instead, strengthen the "fix and retry" instruction.
- Node variant: `execFile` (never `exec`) with the timeout option; the Python interpreter must be on PATH as `python3`/`python`.

## Stretch Goals

- Implement `DockerExecutor` (`docker run --rm --network none --memory 256m -v tmpdir:/code:ro python:3.12-slim python /code/script.py`) and inject it — the agent class shouldn't change at all
- Add a `SecurityPolicy` dataclass: blocklist imports (`os.system`, `subprocess`, `shutil`) by scanning the code before execution
- Give the agent a CSV file path and ask for mean/median/std — data analysis end-to-end
