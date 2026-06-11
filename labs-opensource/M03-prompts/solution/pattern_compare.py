"""
M03 Lab - Step 2: Compare Prompt Patterns — SOLUTION
=====================================================
Run: python pattern_compare.py
"""

from openai import OpenAI

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

CODE = '''def process_items(items):
    result = []
    for i in range(len(items)):
        if items[i] != None:
            result.append(items[i].upper())
    return result'''

patterns = {
    "zero-shot": f"Review this Python code for issues:\n```python\n{CODE}\n```",
    "few-shot": f"""Here are example code reviews:

Code: `x = x + 1` -> Style: Use `x += 1` for augmented assignment.
Code: `if x == None` -> Bug: Use `is None` instead of `== None` for identity checks.

Now review this code:
```python
{CODE}
```""",
    "chain-of-thought": f"""Review this Python code step by step:
```python
{CODE}
```

Think through it methodically:
1. Read each line and check for bugs
2. Look for performance issues
3. Check for style violations
4. Summarize your findings""",
}

for name, prompt in patterns.items():
    try:
        response = client.chat.completions.create(
            model="mistral",
            messages=[{"role": "user", "content": prompt}],
        )
        print(f"\n{'=' * 50}")
        print(f"Pattern: {name}")
        print(
            f"Tokens: {response.usage.prompt_tokens} in, "
            f"{response.usage.completion_tokens} out"
        )
        print(f"Response:\n{response.choices[0].message.content[:300]}")
    except Exception as e:
        print(f"Error ({name}): {e}")
