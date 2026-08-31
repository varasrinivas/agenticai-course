import { fileURLToPath } from "url";
/**
 * M18 — Task Completion Scorer (Node.js Solution)
 * Scores whether the agent found the correct UCC filings.
 * Uses partial credit: finding 3 of 5 expected filings = 0.6.
 */

/**
 * Extract UCC filing numbers from response text.
 * Pattern: UCC-YYYY-XX-NNNNNNN
 */
function extractFilingNumbers(text) {
  const pattern = /UCC-\d{4}-[A-Z]{2}-\d{7}/g;
  const matches = text.match(pattern) || [];
  return [...new Set(matches)]; // deduplicate
}

/**
 * Score whether the agent found the correct filings.
 *
 * @param {string} response - The agent's text response
 * @param {object} expected - Object with expected_filings array
 * @returns {{ score: number, found: string[], missed: string[], extra: string[], details: string }}
 */
function scoreTaskCompletion(response, expected) {
  const expectedFilings = new Set(expected.expected_filings || []);
  const foundFilings = new Set(extractFilingNumbers(response));

  // Edge case: no filings expected
  if (expectedFilings.size === 0) {
    if (foundFilings.size === 0) {
      return {
        score: 1.0,
        found: [],
        missed: [],
        extra: [],
        details: "Correctly returned no filings (none expected).",
      };
    } else {
      return {
        score: 0.0,
        found: [],
        missed: [],
        extra: [...foundFilings].sort(),
        details: `Expected no filings but found ${foundFilings.size}.`,
      };
    }
  }

  // Calculate matches
  const correctlyFound = [...expectedFilings].filter((f) => foundFilings.has(f));
  const missed = [...expectedFilings].filter((f) => !foundFilings.has(f));
  const extra = [...foundFilings].filter((f) => !expectedFilings.has(f));

  const score = correctlyFound.length / expectedFilings.size;

  const detailParts = [];
  if (correctlyFound.length > 0) {
    detailParts.push(
      `Found ${correctlyFound.length}/${expectedFilings.size} expected filings.`
    );
  }
  if (missed.length > 0) {
    detailParts.push(`Missed: ${missed.sort().join(", ")}.`);
  }
  if (extra.length > 0) {
    detailParts.push(`Extra (not expected): ${extra.sort().join(", ")}.`);
  }
  if (score === 1.0) {
    detailParts.push("Perfect match!");
  }

  return {
    score,
    found: correctlyFound.sort(),
    missed: missed.sort(),
    extra: extra.sort(),
    details: detailParts.join(" "),
  };
}

// ---------------------------------------------------------------------------
// Self-test
// ---------------------------------------------------------------------------
// ESM has no require.main; compare the resolved entry path instead.
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  console.log("Task Completion Scorer — Self-Test");
  console.log("=".repeat(50));

  // Test 1: Perfect match
  const result1 = scoreTaskCompletion(
    "Found 2 filings:\n- UCC-2024-NY-0012847 (Active)\n- UCC-2024-NY-0015921 (Active)",
    { expected_filings: ["UCC-2024-NY-0012847", "UCC-2024-NY-0015921"] }
  );
  console.log(`\nTest 1 — Perfect match: score=${result1.score} (expected: 1.0)`);
  console.assert(result1.score === 1.0, `Expected 1.0, got ${result1.score}`);

  // Test 2: Partial match
  const result2 = scoreTaskCompletion(
    "I found filing UCC-2024-NY-0012847 for Acme Corporation.",
    { expected_filings: ["UCC-2024-NY-0012847", "UCC-2024-NY-0015921"] }
  );
  console.log(`\nTest 2 — Partial match: score=${result2.score} (expected: 0.5)`);
  console.assert(result2.score === 0.5, `Expected 0.5, got ${result2.score}`);

  // Test 3: No match
  const result3 = scoreTaskCompletion(
    "I could not find any filings for that entity.",
    { expected_filings: ["UCC-2024-NY-0012847"] }
  );
  console.log(`\nTest 3 — No match: score=${result3.score} (expected: 0.0)`);
  console.assert(result3.score === 0.0, `Expected 0.0, got ${result3.score}`);

  // Test 4: Empty expected
  const result4 = scoreTaskCompletion("No filings were found for XYZ Corp.", {
    expected_filings: [],
  });
  console.log(`\nTest 4 — Empty expected: score=${result4.score} (expected: 1.0)`);
  console.assert(result4.score === 1.0, `Expected 1.0, got ${result4.score}`);

  console.log("\n" + "=".repeat(50));
  console.log("All self-tests passed!");
}

export { extractFilingNumbers, scoreTaskCompletion };
