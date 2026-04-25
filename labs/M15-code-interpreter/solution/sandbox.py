"""
M15 Lab — Sandboxed Python Executor
=====================================
Runs Python code in a subprocess with timeout and limited environment.
Prepends mock UCC filing data as a MOCK_FILINGS variable so that
agent-generated code can analyze it.

This file is COMPLETE — do not modify it.

Usage:
    python sandbox.py          # runs the self-test
    from sandbox import run_in_sandbox
"""

import json
import os
import subprocess
import sys
import tempfile

# Import the data preamble from mock_data
sys.path.insert(0, os.path.dirname(__file__))
from mock_data import DATA_FOR_SANDBOX


def run_in_sandbox(code: str, timeout: int = 10) -> dict:
    """
    Execute Python code in a sandboxed subprocess.

    The code receives a pre-defined MOCK_FILINGS variable (list of dicts)
    containing UCC filing data. It runs in a temporary file with:
      - A hard timeout (default 10 seconds)
      - A stripped-down environment (no inherited secrets)
      - stdout/stderr capture

    Args:
        code:    Python code string to execute.
        timeout: Max execution time in seconds.

    Returns:
        dict with keys:
            stdout     (str)  — captured standard output
            stderr     (str)  — captured standard error
            returncode (int)  — process return code (0 = success)
    """
    # Prepend the data preamble so the code has access to MOCK_FILINGS
    full_code = DATA_FOR_SANDBOX + code

    tmp_path = None
    try:
        # Write to a temporary .py file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(full_code)
            tmp_path = f.name

        # Build a minimal environment — strip secrets, keep PATH for Python
        safe_env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONIOENCODING": "utf-8",
            "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),  # needed on Windows
        }

        # Execute in subprocess with timeout
        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=timeout,
            env=safe_env,
        )

        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }

    except subprocess.TimeoutExpired:
        return {
            "stdout": "",
            "stderr": f"SANDBOX ERROR: Execution timed out after {timeout} seconds.",
            "returncode": -1,
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": f"SANDBOX ERROR: {type(e).__name__}: {str(e)}",
            "returncode": -1,
        }
    finally:
        # Always clean up the temp file
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


# =============================================================================
# SELF-TEST
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Sandbox Self-Test")
    print("=" * 60)

    # Test 1: Simple code execution
    print("\n--- Test 1: Simple print ---")
    result = run_in_sandbox('print("Hello from sandbox!")')
    assert result["returncode"] == 0, f"Expected 0, got {result['returncode']}"
    assert "Hello from sandbox!" in result["stdout"], "Missing output"
    print(f"  stdout: {result['stdout'].strip()}")
    print("  PASS")

    # Test 2: Access MOCK_FILINGS data
    print("\n--- Test 2: Access MOCK_FILINGS ---")
    result = run_in_sandbox('print(f"Total filings: {len(MOCK_FILINGS)}")')
    assert result["returncode"] == 0, f"Expected 0, got {result['returncode']}"
    assert "Total filings: 11" in result["stdout"], f"Unexpected: {result['stdout']}"
    print(f"  stdout: {result['stdout'].strip()}")
    print("  PASS")

    # Test 3: Data analysis
    print("\n--- Test 3: Count by state ---")
    analysis_code = """
from collections import Counter
states = Counter(f['state'] for f in MOCK_FILINGS)
for state, count in sorted(states.items(), key=lambda x: -x[1]):
    print(f"  {state}: {count}")
"""
    result = run_in_sandbox(analysis_code)
    assert result["returncode"] == 0, f"Failed: {result['stderr']}"
    print(f"  stdout:\n{result['stdout']}")
    print("  PASS")

    # Test 4: Timeout enforcement
    print("\n--- Test 4: Timeout (infinite loop) ---")
    result = run_in_sandbox("while True: pass", timeout=2)
    assert result["returncode"] == -1, "Should have timed out"
    assert "timed out" in result["stderr"].lower(), f"Unexpected: {result['stderr']}"
    print(f"  stderr: {result['stderr'].strip()}")
    print("  PASS")

    # Test 5: Syntax error handling
    print("\n--- Test 5: Syntax error ---")
    result = run_in_sandbox("def oops(\n  print('bad')")
    assert result["returncode"] != 0, "Should have failed"
    assert result["stderr"], "Should have stderr"
    print(f"  stderr: {result['stderr'].strip()[:100]}")
    print("  PASS")

    # Test 6: No network / no os.system danger
    print("\n--- Test 6: Restricted environment ---")
    result = run_in_sandbox("import os; print(os.environ.get('ANTHROPIC_API_KEY', 'NOT FOUND'))")
    assert "NOT FOUND" in result["stdout"], "API key should not be accessible"
    print(f"  stdout: {result['stdout'].strip()}")
    print("  PASS")

    print("\n" + "=" * 60)
    print("All sandbox self-tests passed!")
    print("=" * 60)
