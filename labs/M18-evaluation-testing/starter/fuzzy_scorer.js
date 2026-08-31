import { fileURLToPath } from "url";
/**
 * M18 — Fuzzy Entity Match Scorer (Node.js Starter)
 * Scores entity resolution accuracy using token-based fuzzy matching.
 * No external dependencies — uses simple token overlap (Jaccard similarity).
 *
 * TODO: Implement the three functions below.
 */

/**
 * Break a string into lowercase alphanumeric tokens.
 *
 * TODO:
 * 1. Convert to lowercase
 * 2. Split on non-alphanumeric characters
 * 3. Filter out empty strings
 * 4. Return as a Set
 *
 * @param {string} text
 * @returns {Set<string>}
 */
function tokenize(text) {
  // TODO: Implement tokenization
  return new Set();
}

/**
 * Score how well two entity names match using Jaccard similarity.
 * Jaccard = |intersection| / |union|
 *
 * TODO:
 * 1. Tokenize both strings
 * 2. Handle edge cases: both empty -> 1.0, one empty -> 0.0
 * 3. Calculate Jaccard similarity
 *
 * @param {string} responseEntity
 * @param {string} expectedEntity
 * @returns {number} 0.0-1.0
 */
function scoreEntityMatch(responseEntity, expectedEntity) {
  // TODO: Implement Jaccard similarity
  return 0;
}

/**
 * Score entity resolution from the agent response.
 *
 * TODO:
 * 1. If expected_entity is null, return score 1.0
 * 2. Check exact substring match
 * 3. Fall back to token overlap
 * 4. Return { score, matches, details }
 *
 * @param {string} response
 * @param {object} expected - { expected_entity: string | null }
 * @returns {{ score: number, matches: Array, details: string }}
 */
function scoreEntityResolution(response, expected) {
  // TODO: Implement entity resolution scoring
  return { score: 0, matches: [], details: "" };
}

// ---------------------------------------------------------------------------
// Self-test
// ---------------------------------------------------------------------------
// ESM has no require.main; compare the resolved entry path instead.
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  console.log("Fuzzy Entity Match Scorer — Self-Test");
  console.log("=".repeat(50));

  const s1 = scoreEntityMatch("Acme Corporation", "Acme Corporation");
  console.log(`\nTest 1 — Exact: ${s1.toFixed(2)} (expected: 1.00)`);
  console.assert(s1 === 1.0);

  const s2 = scoreEntityMatch("Acme Corp", "Acme Corporation");
  console.log(`Test 2 — Abbrev: ${s2.toFixed(2)} (expected: ~0.33)`);
  console.assert(s2 >= 0.3 && s2 <= 0.7);

  const s3 = scoreEntityMatch("Totally Different", "Acme Corporation");
  console.log(`Test 3 — No match: ${s3.toFixed(2)} (expected: 0.00)`);
  console.assert(s3 === 0.0);

  const r5 = scoreEntityResolution(
    "I found filings for Acme Corporation in NY.",
    { expected_entity: "Acme Corporation" }
  );
  console.log(`\nTest 5 — Entity in response: ${r5.score.toFixed(2)} (expected: >= 0.5)`);
  console.assert(r5.score >= 0.5);

  console.log("\n" + "=".repeat(50));
  console.log("All self-tests passed!");
}

export { tokenize, scoreEntityMatch, scoreEntityResolution };
