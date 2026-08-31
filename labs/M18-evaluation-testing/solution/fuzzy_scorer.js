import { fileURLToPath } from "url";
/**
 * M18 — Fuzzy Entity Match Scorer (Node.js Solution)
 * Scores entity resolution accuracy using token-based fuzzy matching.
 * No external dependencies — uses simple token overlap (Jaccard similarity).
 */

/**
 * Break a string into lowercase alphanumeric tokens.
 * @param {string} text
 * @returns {Set<string>}
 */
function tokenize(text) {
  const tokens = text
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter((t) => t.length > 0);
  return new Set(tokens);
}

/**
 * Score how well two entity names match using Jaccard similarity.
 * Jaccard = |intersection| / |union|
 *
 * @param {string} responseEntity
 * @param {string} expectedEntity
 * @returns {number} 0.0-1.0
 */
function scoreEntityMatch(responseEntity, expectedEntity) {
  const tokensA = tokenize(responseEntity);
  const tokensB = tokenize(expectedEntity);

  if (tokensA.size === 0 && tokensB.size === 0) return 1.0;
  if (tokensA.size === 0 || tokensB.size === 0) return 0.0;

  const intersection = new Set([...tokensA].filter((t) => tokensB.has(t)));
  const union = new Set([...tokensA, ...tokensB]);

  return intersection.size / union.size;
}

/**
 * Score entity resolution from the agent response.
 *
 * @param {string} response - The agent's text response
 * @param {object} expected - Object with expected_entity (string or null)
 * @returns {{ score: number, matches: Array, details: string }}
 */
function scoreEntityResolution(response, expected) {
  const expectedEntity = expected.expected_entity;

  if (expectedEntity === null || expectedEntity === undefined) {
    return {
      score: 1.0,
      matches: [],
      details: "No entity check required (expected_entity is null).",
    };
  }

  // Exact substring match
  if (response.toLowerCase().includes(expectedEntity.toLowerCase())) {
    return {
      score: 1.0,
      matches: [
        {
          response_entity: expectedEntity,
          expected_entity: expectedEntity,
          similarity: 1.0,
        },
      ],
      details: `Exact match: '${expectedEntity}' found in response.`,
    };
  }

  // Fuzzy: token overlap between expected entity and full response
  const responseTokens = tokenize(response);
  const expectedTokens = tokenize(expectedEntity);

  if (expectedTokens.size === 0) {
    return { score: 1.0, matches: [], details: "Expected entity has no tokens." };
  }

  const overlap = new Set(
    [...expectedTokens].filter((t) => responseTokens.has(t))
  );
  const similarity = overlap.size / expectedTokens.size;
  const score = Math.min(similarity, 1.0);

  const matches = [];
  if (similarity > 0) {
    matches.push({
      response_entity: [...overlap].sort().join(" "),
      expected_entity: expectedEntity,
      similarity: Math.round(similarity * 1000) / 1000,
    });
  }

  let details;
  if (score >= 0.8) {
    details = `Strong match (${(score * 100).toFixed(0)}%): most tokens of '${expectedEntity}' found.`;
  } else if (score >= 0.5) {
    details = `Partial match (${(score * 100).toFixed(0)}%): some tokens of '${expectedEntity}' found.`;
  } else {
    details = `Weak match (${(score * 100).toFixed(0)}%): few tokens of '${expectedEntity}' found.`;
  }

  return {
    score: Math.round(score * 1000) / 1000,
    matches,
    details,
  };
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
  console.log(`\nTest 2 — Abbreviation: ${s2.toFixed(2)} (expected: ~0.33)`);
  console.assert(s2 >= 0.3 && s2 <= 0.7);

  const s3 = scoreEntityMatch("Totally Different Company", "Acme Corporation");
  console.log(`\nTest 3 — No match: ${s3.toFixed(2)} (expected: 0.00)`);
  console.assert(s3 === 0.0);

  const r5 = scoreEntityResolution(
    "I found filings for Acme Corporation in New York.",
    { expected_entity: "Acme Corporation" }
  );
  console.log(`\nTest 5 — Entity in response: ${r5.score.toFixed(2)} (expected: >= 0.5)`);
  console.assert(r5.score >= 0.5);

  const r6 = scoreEntityResolution("Some response", { expected_entity: null });
  console.log(`\nTest 6 — No expected entity: ${r6.score.toFixed(2)} (expected: 1.00)`);
  console.assert(r6.score === 1.0);

  console.log("\n" + "=".repeat(50));
  console.log("All self-tests passed!");
}

export { tokenize, scoreEntityMatch, scoreEntityResolution };
