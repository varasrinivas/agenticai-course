"""
M15 Lab - Step 2: The Self-Debugging Code Agent — SOLUTION
===========================================================
Run: python code_agent.py
"""

import json

from openai import OpenAI
from sandbox_executor import SubprocessExecutor

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

EXECUTE_PYTHON_TOOL = {
    "type": "function",
    "function": {
        "name": "execute_python",
        "description": (
            "Execute Python code in a sandbox and return stdout, stderr, and "
            "exit_code. Use print() for any output you want to see."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Complete, runnable Python code"},
                "timeout_seconds": {"type": "integer", "description": "Max runtime (default 10)"},
            },
            "required": ["code"],
        },
    },
}

SYSTEM_PROMPT = (
    "You are a data analysis assistant. When asked to compute something, "
    "write complete Python code and call execute_python. Always import every "
    "module you use. Print your final answer so it appears in stdout. If you "
    "receive an error, read it carefully, fix the code, and call "
    "execute_python again."
)


class CodeExecutionAgent:
    """ReAct-style agent that writes code, runs it, and self-debugs."""

    def __init__(self, executor=None, model: str = "mistral", max_retries: int = 3):
        self.executor = executor or SubprocessExecutor()
        self.model = model
        self.max_retries = max_retries

    def run(self, user_request: str) -> str:
        """Run the agent, return the final answer string."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_request},
        ]
        result = None

        for attempt in range(self.max_retries + 1):
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=[EXECUTE_PYTHON_TOOL],
                    tool_choice="auto",
                    temperature=0.1,  # low temp = more deterministic code
                )
            except Exception as e:
                return f"API error: {e}"

            msg = response.choices[0].message

            # Some Ollama builds drop tool_choice silently — check tool_calls
            if not msg.tool_calls:
                return msg.content or "(no output)"

            messages.append(msg)  # assistant message FIRST, then results

            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments)
                code = args["code"]
                result = self.executor.run(code, args.get("timeout_seconds", 10))
                first_line = code.strip().splitlines()[0][:60] if code.strip() else ""
                print(f"  [attempt {attempt + 1}] ran: {first_line}...  exit={result.exit_code}")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result.to_tool_content(),
                })

            if attempt == self.max_retries and result and result.exit_code != 0:
                return (
                    f"Failed after {self.max_retries} attempts.\n"
                    f"Last error:\n{result.stderr}"
                )

        # Final summary call without tools
        try:
            response = client.chat.completions.create(
                model=self.model, messages=messages, temperature=0.1
            )
            return response.choices[0].message.content or "(no output)"
        except Exception as e:
            return f"API error during summary: {e}"


if __name__ == "__main__":
    agent = CodeExecutionAgent()

    print("TEST 1: computation the model can't do in its head")
    answer = agent.run("What is 3.7 to the power of 12? Show your work.")
    print(f"\nAgent answer: {answer[:300]}")

    print("\nTEST 2: a task that usually needs a debug round")
    answer = agent.run(
        "Compute the 25th Fibonacci number and the sum of the first 25 "
        "Fibonacci numbers. Print both."
    )
    print(f"\nAgent answer: {answer[:300]}")
