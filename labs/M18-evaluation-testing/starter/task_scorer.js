import { fileURLToPath } from "url";
import assert from "node:assert/strict";
/**
 * M18 — Task Completion Scorer (Node.js Starter)
 * Scores whether the agent found the correct UCC filings.
 * Uses partial credit: finding 3 of 5 expected filings = 0.6.
 *
 * TODO: Implement the two functions below.
 */

/**
 * Extract UCC filing numbers from response text.
 * Pattern: UCC-YYYY-XX-NNNNNNN
 *
 * TODO:
 * 1. Use a regex pattern to find all filing numbers
 * 2. Return a deduplicated array
 * 3. Handle edge cases: no matches, duplicates
 *
 * @param {string} text
 * @returns {string[]}
 */
function extractFilingNumbers(text) {
  // TODO: Implement regex extraction
  return [];
}

/**
 * Score whether the agent found the correct filings.
 *
 * TODO:
 * 1. Extract filing numbers from response using extractFilingNumbers()
 * 2. Compare against expected.expected_filings
 * 3. Partial credit: found / expected count
 * 4. Handle edge case: empty expected list
 * 5. Return { score, found, missed, extra, details }
 *
 * @param {string} response
 * @param {object} expected - { expected_filings: string[] }
 * @returns {{ score: number, found: string[], missed: string[], extra: string[], details: string }}
 */
function scoreTaskCompletion(response, expected) {
  // TODO: Implement scoring logic
  return { score: 0, found: [], missed: [], extra: [], details: "" };
}

// ---------------------------------------------------------------------------
// Self-test
// ---------------------------------------------------------------------------
// ESM has no require.main; compare the resolved entry path instead.
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  console.log("Task Completion Scorer — Self-Test");
  console.log("=".repeat(50));

  // Test 1: Perfect match
  const r1 = scoreTaskCompletion(
    "Found:\n- UCC-2024-NY-0012847\n- UCC-2024-NY-0015921",
    { expected_filings: ["UCC-2024-NY-0012847", "UCC-2024-NY-0015921"] }
  );
  console.log(`\nTest 1 — Perfect match: score=${r1.score} (expected: 1.0)`);
  assert.ok(r1.score === 1.0);

  // Test 2: Partial
  const r2 = scoreTaskCompletion(
    "Found UCC-2024-NY-0012847.",
    { expected_filings: ["UCC-2024-NY-0012847", "UCC-2024-NY-0015921"] }
  );
  console.log(`Test 2 — Partial: score=${r2.score} (expected: 0.5)`);
  assert.ok(r2.score === 0.5);

  // Test 3: None
  const r3 = scoreTaskCompletion("No filings.", { expected_filings: ["UCC-2024-NY-0012847"] });
  console.log(`Test 3 — None: score=${r3.score} (expected: 0.0)`);
  assert.ok(r3.score === 0.0);

  // Test 4: Empty expected
  const r4 = scoreTaskCompletion("No filings found.", { expected_filings: [] });
  console.log(`Test 4 — Empty expected: score=${r4.score} (expected: 1.0)`);
  assert.ok(r4.score === 1.0);

  console.log("\n" + "=".repeat(50));
  console.log("All self-tests passed!");
}

export { extractFilingNumbers, scoreTaskCompletion };
