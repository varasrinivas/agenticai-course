/**
 * M03 Lab - Step 1: Code Review System Prompt — SOLUTION
 * =======================================================
 * Run: node review_agent.js
 */

import OpenAI from "openai";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

const REVIEW_SYSTEM_PROMPT = `You are a senior software engineer conducting code reviews.

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
<tone>Be constructive and specific. Praise good patterns. Never be dismissive.</tone>`;

// Test code with a deliberate SQL injection vulnerability
const testCode = `def get_user(id):
    query = f"SELECT * FROM users WHERE id = {id}"
    return db.execute(query)`;

try {
  const response = await client.chat.completions.create({
    model: "mistral",
    messages: [
      { role: "system", content: REVIEW_SYSTEM_PROMPT },
      { role: "user", content: `Review this code:\n\`\`\`python\n${testCode}\n\`\`\`` },
    ],
  });
  console.log(response.choices[0].message.content);
  console.log(
    `\nTokens: ${response.usage.prompt_tokens} in, ${response.usage.completion_tokens} out`
  );
} catch (error) {
  console.error(`API error: ${error.message}`);
  console.error("Is Ollama running? Try: ollama serve");
}
