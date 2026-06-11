/**
 * M03 Lab - Step 2: Compare Prompt Patterns — SOLUTION
 * =====================================================
 * Run: node pattern_compare.js
 */

import OpenAI from "openai";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

const CODE = `def process_items(items):
    result = []
    for i in range(len(items)):
        if items[i] != None:
            result.append(items[i].upper())
    return result`;

const patterns = {
  "zero-shot": `Review this Python code for issues:\n\`\`\`python\n${CODE}\n\`\`\``,
  "few-shot": `Here are example code reviews:

Code: \`x = x + 1\` -> Style: Use \`x += 1\` for augmented assignment.
Code: \`if x == None\` -> Bug: Use \`is None\` instead of \`== None\` for identity checks.

Now review this code:
\`\`\`python
${CODE}
\`\`\``,
  "chain-of-thought": `Review this Python code step by step:
\`\`\`python
${CODE}
\`\`\`

Think through it methodically:
1. Read each line and check for bugs
2. Look for performance issues
3. Check for style violations
4. Summarize your findings`,
};

for (const [name, prompt] of Object.entries(patterns)) {
  try {
    const response = await client.chat.completions.create({
      model: "mistral",
      messages: [{ role: "user", content: prompt }],
    });
    console.log(`\n${"=".repeat(50)}`);
    console.log(`Pattern: ${name}`);
    console.log(
      `Tokens: ${response.usage.prompt_tokens} in, ${response.usage.completion_tokens} out`
    );
    console.log(`Response:\n${response.choices[0].message.content.slice(0, 300)}`);
  } catch (error) {
    console.error(`Error (${name}): ${error.message}`);
  }
}
