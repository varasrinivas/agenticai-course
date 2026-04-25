/**
 * M18 — Claude-as-Judge Scorer (Node.js Starter)
 * Uses a SEPARATE Claude call to evaluate response quality on a rubric.
 * Supports mock mode for testing without API calls.
 *
 * TODO: Implement the two functions below.
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
- 0: Completely wrong or fabricated

**Completeness (0-5)**:
- 5: Covers all expected items; nothing missing
- 3: Covers most expected items but misses 1-2 key details
- 0: Almost nothing relevant

**Clarity (0-5)**:
- 5: Well-structured, easy to read, professional
- 3: Readable but could be better organized
- 0: Incoherent

Respond with ONLY a JSON object:
{
    "accuracy": <0-5>,
    "completeness": <0-5>,
    "clarity": <0-5>,
    "reasoning": "<1-2 sentence explanation>"
}`;

/**
 * Mock judge score using simple heuristics.
 *
 * TODO:
 * 1. Check if expected filing numbers appear in response -> accuracy
 * 2. Check if key_facts appear in response -> completeness
 * 3. Check response length/structure -> clarity
 * 4. Normalize to 0.0-1.0 and return structured result
 *
 * @param {string} query
 * @param {string} response
 * @param {object} expected
 * @returns {{ score: number, accuracy: number, completeness: number, clarity: number, reasoning: string }}
 */
function mockJudgeScore(query, response, expected) {
  // TODO: Implement mock scoring heuristics
  return { score: 0, accuracy: 0, completeness: 0, clarity: 0, reasoning: "" };
}

/**
 * Score response quality using Claude as judge.
 *
 * TODO:
 * 1. If mockMode, call mockJudgeScore() and return
 * 2. If live mode:
 *    a. Check anthropic SDK and API key
 *    b. Build judge prompt with query, response, expected
 *    c. Call Claude with JUDGE_SYSTEM_PROMPT
 *    d. Parse JSON response
 *    e. Normalize score = (accuracy + completeness + clarity) / 15
 * 3. Handle errors gracefully
 *
 * @param {string} query
 * @param {string} response
 * @param {object} expected
 * @param {boolean} mockMode
 * @returns {Promise<{score: number, accuracy: number, completeness: number, clarity: number, reasoning: string}>}
 */
async function scoreWithJudge(query, response, expected, mockMode = true) {
  // TODO: Implement judge scoring
  return { score: 0, accuracy: 0, completeness: 0, clarity: 0, reasoning: "" };
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
      "Found 2 filings:\n- **UCC-2024-NY-0012847** — Atlantic Capital Partners\n" +
      "- **UCC-2024-NY-0015921** — Citibank N.A.\nAccounts receivable collateral.";
    const responseBad = "I don't know.";
    const expected = {
      expected_filings: ["UCC-2024-NY-0012847", "UCC-2024-NY-0015921"],
      key_facts: ["Atlantic Capital Partners", "Citibank N.A.", "accounts receivable"],
    };

    const r1 = await scoreWithJudge(query, responseGood, expected, true);
    console.log(`\nTest 1 — Good (mock): score=${r1.score.toFixed(2)}`);
    console.assert(r1.score >= 0.5, `Expected >= 0.5, got ${r1.score}`);

    const r2 = await scoreWithJudge(query, responseBad, expected, true);
    console.log(`Test 2 — Bad (mock): score=${r2.score.toFixed(2)}`);
    console.assert(r2.score < r1.score, "Bad should score lower");

    console.log("\n" + "=".repeat(50));
    console.log("All self-tests passed!");
  })();
}

module.exports = { scoreWithJudge, mockJudgeScore };
