"""
M03 Lab - Step 1: Code Review System Prompt — SOLUTION
=======================================================
Run: python review_agent.py
"""

from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

REVIEW_SYSTEM_PROMPT = """You are a senior software engineer conducting code reviews.

<role>You review code for correctness, performance, security, and style.</role>
<expertise>Python, JavaScript, SQL. You know OWASP top 10 and PEP 8.</expertise>
<review_criteria>
- Bugs: logic errors, off-by-one, null handling
- Performance: unnecessary loops, missing caching opportunities
- Security: injection risks, hardcoded secrets, unsafe deserialization
- Style: naming conventions, function length, missing docstrings
</review_criteria>
<output_format>
For each category with findings, use this format:
## [Category]
- **Issue**: description
- **Fix**: suggested code change
If a category has no issues, omit it entirely.
</output_format>
<tone>Be constructive and specific. Praise good patterns. Never be dismissive.</tone>"""

# Test code with a deliberate SQL injection vulnerability
test_code = '''def get_user(id):
    query = f"SELECT * FROM users WHERE id = {id}"
    return db.execute(query)'''

try:
    response = client.chat.completions.create(
        model="mistral",
        messages=[
            {"role": "system", "content": REVIEW_SYSTEM_PROMPT},
            {"role": "user", "content": f"Review this code:\n```python\n{test_code}\n```"},
        ],
    )
    print(response.choices[0].message.content)
    print(
        f"\nTokens: {response.usage.prompt_tokens} in, "
        f"{response.usage.completion_tokens} out"
    )
except Exception as e:
    print(f"API error: {e}")
    print("Is Ollama running? Try: ollama serve")
