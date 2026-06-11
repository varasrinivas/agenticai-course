"""
M15 Lab - Step 1: SubprocessExecutor — SOLUTION
================================================
Run: python sandbox_executor.py
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
        """Format the result as a concise tool message for the model."""
        lines = [f"exit_code: {self.exit_code}"]
        if self.stdout:
            lines.append(f"stdout:\n{self.stdout.strip()}")
        if self.stderr:
            lines.append(f"stderr:\n{self.stderr.strip()}")
        return "\n".join(lines)


class SubprocessExecutor:
    """Runs Python code in a child process.

    Dev-tier sandbox: zero Docker overhead, but FULL filesystem access.
    Never use for untrusted user input — upgrade to DockerExecutor.
    """

    def __init__(self, timeout_seconds: int = 10):
        self.timeout_seconds = timeout_seconds

    def run(self, code: str, timeout: int | None = None) -> ExecResult:
        """Execute code, return ExecResult. Never raises."""
        timeout = timeout or self.timeout_seconds

        # Temp file gives the child its own scope; delete=False so the
        # child can open it after we close it.
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            tmp_path = f.name

        try:
            result = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False,  # CRITICAL: never True (shell injection)
            )
            return ExecResult(
                stdout=result.stdout,
                stderr=result.stderr,
                exit_code=result.returncode,
            )
        except subprocess.TimeoutExpired:
            return ExecResult(
                stdout="",
                stderr=f"Execution timed out after {timeout} seconds.",
                exit_code=124,  # bash timeout(1) convention
            )
        except Exception as e:
            return ExecResult(stdout="", stderr=str(e), exit_code=1)
        finally:
            os.unlink(tmp_path)  # cleanup even on crash


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
