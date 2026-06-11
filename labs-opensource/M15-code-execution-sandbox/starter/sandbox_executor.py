"""
M15 Lab - Step 1: SubprocessExecutor
=====================================
Run model-written Python in a child process with a timeout.
Run: python sandbox_executor.py    (smoke tests, no LLM needed)
"""

import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass


@dataclass
class ExecResult:
    stdout: str
    stderr: str
    exit_code: int

    def to_tool_content(self) -> str:
        """(COMPLETE) Format the result as a concise tool message for the model."""
        lines = [f"exit_code: {self.exit_code}"]
        if self.stdout:
            lines.append(f"stdout:\n{self.stdout.strip()}")
        if self.stderr:
            lines.append(f"stderr:\n{self.stderr.strip()}")
        return "\n".join(lines)


class SubprocessExecutor:
    """Runs Python code in a child process.

    Dev-tier sandbox: zero Docker overhead, but FULL filesystem access.
    Never use for untrusted user input — upgrade to DockerExecutor (stretch).
    """

    def __init__(self, timeout_seconds: int = 10):
        self.timeout_seconds = timeout_seconds

    def run(self, code: str, timeout: int | None = None) -> ExecResult:
        """Execute code, return ExecResult. Must never raise.

        TODO:
        1. timeout = timeout or self.timeout_seconds
        2. Write `code` to a NamedTemporaryFile(mode="w", suffix=".py",
           delete=False, encoding="utf-8") — keep the .name as tmp_path.
           WHY a temp file: exec(code) in-process would pollute our namespace.
           WHY delete=False: the child must be able to open it after we close it.
        3. try:
             result = subprocess.run([sys.executable, tmp_path],
                 capture_output=True, text=True, timeout=timeout,
                 shell=False)   ← CRITICAL: never shell=True (injection)
             return ExecResult(result.stdout, result.stderr, result.returncode)
           except subprocess.TimeoutExpired:
             return ExecResult("", f"Execution timed out after {timeout} seconds.",
                               124)   ← bash timeout(1) convention
           except Exception as e:
             return ExecResult("", str(e), 1)
           finally:
             os.unlink(tmp_path)   ← cleanup even on crash
        """
        pass  # Remove this line when you add your code


# ── Smoke tests (COMPLETE) ──
if __name__ == "__main__":
    ex = SubprocessExecutor(timeout_seconds=3)

    print("TEST 1: happy path")
    r = ex.run("print(sum(range(101)))")
    print(f"  {r.to_tool_content()}")
    assert r.exit_code == 0 and "5050" in r.stdout

    print("\nTEST 2: deliberate NameError (must return, not raise)")
    r = ex.run("print(undefined_variable)")
    print(f"  exit_code={r.exit_code}, stderr contains NameError: {'NameError' in r.stderr}")
    assert r.exit_code != 0 and "NameError" in r.stderr

    print("\nTEST 3: infinite loop (must time out at exit code 124, not hang)")
    r = ex.run("while True: pass")
    print(f"  exit_code={r.exit_code}, stderr={r.stderr[:50]}")
    assert r.exit_code == 124

    print("\nAll executor checks passed.")
