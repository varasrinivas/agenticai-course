"""
M03 Lab - Step 1: Code Review System Prompt
============================================
Write a structured system prompt and test it on code with a real vulnerability.
Run: python review_agent.py
"""

from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

# TODO: Write a system prompt with four labeled sections:
# <role>            — senior software engineer reviewing for correctness,
#                     performance, security, and style
# <review_criteria> — name concrete things to check: logic errors, injection
#                     risks, hardcoded secrets, naming, missing docstrings...
# <output_format>   — "## [Category]" headers, **Issue**/**Fix** bullets,
#                     omit categories with no findings
# <tone>            — constructive and specific; praise good patterns
REVIEW_SYSTEM_PROMPT = """..."""

# Test code with a deliberate SQL injection vulnerability (COMPLETE)
test_code = '''def get_user(id):
    query = f"SELECT * FROM users WHERE id = {id}"
    return db.execute(query)'''

# TODO: Send the review request:
# - messages: [{"role": "system", "content": REVIEW_SYSTEM_PROMPT},
#              {"role": "user", "content": f"Review this code:\n```python\n{test_code}\n```"}]
# - Print the response and token usage (usage.prompt_tokens / usage.completion_tokens)
# - try/except with a helpful error message
#
# Success check: the response must flag the f-string SQL injection.
# If it doesn't, make <review_criteria> more explicit and re-run.

pass  # Remove this line when you add your code
