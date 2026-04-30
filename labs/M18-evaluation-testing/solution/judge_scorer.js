/**
 * M18 — Claude-as-Judge Scorer (Node.js Solution)
 * Uses a SEPARATE Claude call to evaluate response quality on a rubric.
 * Supports mock mode for testing without API calls.
 */

let Anthropic;
let HAS_ANTHROPIC = false;
try {
  Anthropic = require("@anthropic-ai/sdk").default || require("@anthropic-ai/sdk");
  HAS_ANTHROPIC = true;
} catch {
  HAS_ANTHROPIC = false;
}

const JUDGE_SYSTEM_PROMPT = `You are an expert evaluator for a UCC filing research agent.
Your job is to score the agent's response on three dimensions.

Score each dimension from 0 to 5:

**Accuracy (0-5)**:
- 5: All facts are correct, all filing numbers accurate, all entity names exact
- 3: Mostly correct with minor errors
- 1: Significant factual errors
- 0: Completely wrong or fabricated information

**Completeness (0-5)**:
- 5: Covers all expected filings, entities, and key facts; nothing missing
- 3: Covers most expected items but misses 1-2 key details
- 1: Major omissions
- 0: Almost nothing relevant included

**Clarity (0-5)**:
- 5: Well-structured, easy to read, professional formatting
- 3: Readable but could be better organized
- 1: Confusing, poorly structured
- 0: Incoherent or unreadable

Respond with ONLY a JSON object:
{
    "accuracy": <0-5>,
    "completeness": <0-5>,
    "clarity": <0-5>,
    "reasoning": "<1-2 sentence explanation>"
}`;

/**
 * Mock judge score using simple heuristics.
 */
function mockJudgeScore(query, response, expected) {
  const expectedFilings = expected.expected_filings || [];
  let accuracy;

  if (expectedFilings.length > 0) {
    const filingsFound = expectedFilings.filter((f) => response.includes(f)).length;
    accuracy = Math.round((filingsFound / expectedFilings.length) * 5);
  } else {
    const hasFilings = /UCC-\d{4}-[A-Z]{2}-\d{7}/.test(response);
    accuracy = hasFilings ? 0 : 5;
  }

  const keyFacts = expected.key_facts || [];
  let completeness;
  if (keyFacts.length > 0) {
    const factsFound = keyFacts.filter((f) =>
      response.toLowerCase().includes(f.toLowerCase())
    ).length;
    completeness = Math.round((factsFound / keyFacts.length) * 5);
  } else {
    completeness = response.length > 20 ? 5 : 3;
  }

  let clarity;
  if (response.length > 100 && (response.includes("\n") || response.includes("**"))) {
    clarity = 5;
  } else if (response.length > 50) {
    clarity = 4;
  } else if (response.length > 20) {
    clarity = 3;
  } else {
    clarity = 1;
  }

  accuracy = Math.max(0, Math.min(5, accuracy));
  completeness = Math.max(0, Math.min(5, completeness));
  clarity = Math.max(0, Math.min(5, clarity));

  const overall = (accuracy + completeness + clarity) / 15.0;

  return {
    score: Math.round(overall * 1000) / 1000,
    accuracy,
    completeness,
    clarity,
    reasoning: `Mock judge: accuracy from ${expectedFilings.length} filings, completeness from ${keyFacts.length} key facts.`,
  };
}

/**
 * Score response quality using Claude as judge.
 *
 * @param {string} query - Original user question
 * @param {string} response - Agent response
 * @param {object} expected - Expected output
 * @param {boolean} mockMode - If true, use mock scoring
 * @returns {Promise<{score: number, accuracy: number, completeness: number, clarity: number, reasoning: string}>}
 */
async function scoreWithJudge(query, response, expected, mockMode = true) {
  if (mockMode) {
    return mockJudgeScore(query, response, expected);
  }

  if (!HAS_ANTHROPIC) {
    return {
      score: 0.0,
      accuracy: 0,
      completeness: 0,
      clarity: 0,
      reasoning: "Error: @anthropic-ai/sdk not installed. Run: npm install @anthropic-ai/sdk",
    };
  }

  const apiKey = process.env.ANTHROPIC_API_KEY || "";
  if (!apiKey) {
    return {
      score: 0.0,
      accuracy: 0,
      completeness: 0,
      clarity: 0,
      reasoning: "Error: ANTHROPIC_API_KEY not set.",
    };
  }

  try {
    const client = new Anthropic({ apiKey });
    const userPrompt =
      `## User Query\n${query}\n\n` +
      `## Agent Response\n${response}\n\n` +
      `## Expected Output\n${JSON.stringify(expected, null, 2)}\n\n` +
      `Score the agent's response. Respond with ONLY a JSON object.`;

    const message = await client.messages.create({
      model: "claude-sonnet-4-6",
      max_tokens: 300,
      system: JUDGE_SYSTEM_PROMPT,
      messages: [{ role: "user", content: userPrompt }],
    });

    const text = message.content[0].text.trim();
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    const scores = JSON.parse(jsonMatch ? jsonMatch[0] : text);

    const accuracy = Math.max(0, Math.min(5, parseInt(scores.accuracy) || 0));
    const completeness = Math.max(0, Math.min(5, parseInt(scores.completeness) || 0));
    const clarity = Math.max(0, Math.min(5, parseInt(scores.clarity) || 0));

    return {
      score: Math.round(((accuracy + completeness + clarity) / 15.0) * 1000) / 1000,
      accuracy,
      completeness,
      clarity,
      reasoning: scores.reasoning || "No reasoning provided.",
    };
  } catch (e) {
    return {
      score: 0.0,
      accuracy: 0,
      completeness: 0,
      clarity: 0,
      reasoning: `Error calling Claude judge: ${e.message}`,
    };
  }
}

// ---------------------------------------------------------------------------
// Self-test
// ---------------------------------------------------------------------------
if (require.main === module) {
  (async () => {
    console.log("Claude-as-Judge Scorer — Self-Test");
    console.log("=".repeat(50));

    const query = "Find all UCC filings for Acme Corporation in New York.";
    const responseGood =
      "I found 2 UCC filings for Acme Corporation in New York:\n\n" +
      "1. **UCC-2024-NY-0012847** — Atlantic Capital Partners\n" +
      "2. **UCC-2024-NY-0015921** — Citibank N.A.\n" +
      "Collateral includes accounts receivable and deposit accounts.";
    const responseBad = "I don't know.";
    const expected = {
      expected_filings: ["UCC-2024-NY-0012847", "UCC-2024-NY-0015921"],
      expected_entity: "Acme Corporation",
      key_facts: ["Atlantic Capital Partners", "Citibank N.A.", "accounts receivable"],
    };

    const r1 = await scoreWithJudge(query, responseGood, expected, true);
    console.log(`\nTest 1 — Good (mock): score=${r1.score.toFixed(2)}`);
    console.assert(r1.score >= 0.5);

    const r2 = await scoreWithJudge(query, responseBad, expected, true);
    console.log(`Test 2 — Bad (mock): score=${r2.score.toFixed(2)}`);
    console.assert(r2.score < r1.score);

    console.log("\n" + "=".repeat(50));
    console.log("All self-tests passed!");
  })();
}

module.exports = { scoreWithJudge, mockJudgeScore };
