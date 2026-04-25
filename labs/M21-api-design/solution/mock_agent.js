/**
 * M21: Mock UCC Agent — Node.js Solution
 * Provides realistic agent responses without requiring an Anthropic API key.
 *
 * Functions:
 *   mockQuery(query)  -> Promise<object>  — synchronous-style response
 *   mockStream(query) -> AsyncGenerator    — yields string chunks
 */

// ---------------------------------------------------------------------------
// Canned responses keyed by query pattern
// ---------------------------------------------------------------------------
const CANNED_RESPONSES = {
  acme: {
    answer:
      "I found 2 UCC filings potentially related to Acme Corporation in New York.\n\n" +
      "1. **UCC-2024-NY-0012847** — Greenfield Logistics LLC (debtor) with " +
      "Atlantic Capital Partners (secured party). Filed 2024-03-15, covering all " +
      "accounts receivable, inventory, equipment, and general intangibles. Status: Active.\n\n" +
      "2. **UCC-2022-DE-0002914** — Nextera Holdings Corp (debtor) with JPMorgan Chase " +
      "Bank N.A. (secured party). Filed 2022-04-30, covering all assets. Status: Active.\n\n" +
      "Note: No exact match for 'Acme Corporation' was found. The results above are " +
      "the closest matches based on entity resolution. You may want to verify the " +
      "legal entity name in the state's filing database.",
    sources: ["UCC-2024-NY-0012847", "UCC-2022-DE-0002914"],
    tokens_used: 1247,
  },
  risk: {
    answer:
      "**Risk Assessment Summary**\n\n" +
      "Based on the UCC filing analysis, here is the risk profile:\n\n" +
      "- **Lien Count:** 3 active filings identified\n" +
      "- **Collateral Coverage:** Broad — includes 'all assets' clauses in 2 filings\n" +
      "- **Risk Level:** MEDIUM-HIGH\n\n" +
      "**Key Concerns:**\n" +
      "1. Multiple secured parties have claims on overlapping collateral\n" +
      "2. One filing covers 'all assets' which creates subordination risk\n" +
      "3. No terminated filings found — all liens are currently active\n\n" +
      "**Recommendation:** Obtain a full lien search from the state filing office " +
      "and request payoff letters from existing secured parties before proceeding.",
    sources: ["UCC-2024-NY-0012847", "UCC-2024-CA-0098231", "UCC-2022-DE-0002914"],
    tokens_used: 1583,
  },
  default: {
    answer:
      "I searched the UCC filing database and found the following results:\n\n" +
      "1. **UCC-2024-NY-0012847** — Greenfield Logistics LLC → Atlantic Capital Partners. " +
      "Active filing in New York covering accounts receivable, inventory, and equipment.\n\n" +
      "2. **UCC-2024-CA-0098231** — Pacific Ridge Technologies Inc → Silicon Valley Bank. " +
      "Active filing in California covering all assets including IP.\n\n" +
      "3. **UCC-2023-TX-0187634** — Lone Star Energy Solutions LP → Wells Fargo Equipment " +
      "Finance. Active filing in Texas covering specific heavy equipment.\n\n" +
      "The search returned 3 active filings across 3 states. Would you like me to " +
      "drill into any specific filing or run a risk assessment?",
    sources: ["UCC-2024-NY-0012847", "UCC-2024-CA-0098231", "UCC-2023-TX-0187634"],
    tokens_used: 1102,
  },
};

function selectResponse(query) {
  const lower = query.toLowerCase();
  if (lower.includes("risk") || lower.includes("assess")) return CANNED_RESPONSES.risk;
  if (lower.includes("acme")) return CANNED_RESPONSES.acme;
  return CANNED_RESPONSES.default;
}

// ---------------------------------------------------------------------------
// Helper: sleep for ms milliseconds
// ---------------------------------------------------------------------------
function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// ---------------------------------------------------------------------------
// Synchronous-style query (returns a Promise)
// ---------------------------------------------------------------------------
async function mockQuery(query) {
  // Simulate latency (0.5-2.0 seconds)
  const latency = 500 + Math.random() * 1500;
  await sleep(latency);

  const response = selectResponse(query);
  return {
    answer: response.answer,
    sources: response.sources,
    tokens_used: response.tokens_used,
  };
}

// ---------------------------------------------------------------------------
// Streaming query (async generator)
// ---------------------------------------------------------------------------
async function* mockStream(query) {
  const response = selectResponse(query);
  const words = response.answer.split(" ");

  let pos = 0;
  while (pos < words.length) {
    const chunkSize = 3 + Math.floor(Math.random() * 6); // 3-8 words
    const chunkWords = words.slice(pos, pos + chunkSize);
    let chunk = chunkWords.join(" ");

    if (pos + chunkSize < words.length) {
      chunk += " ";
    }

    yield chunk;

    // Simulate streaming latency (50-200ms)
    await sleep(50 + Math.random() * 150);
    pos += chunkSize;
  }
}

// ---------------------------------------------------------------------------
// Exports
// ---------------------------------------------------------------------------
module.exports = { mockQuery, mockStream };

// ---------------------------------------------------------------------------
// Self-test
// ---------------------------------------------------------------------------
if (require.main === module) {
  (async () => {
    console.log("=== Mock Agent Test (Node.js) ===\n");

    console.log("1. Synchronous query:");
    const result = await mockQuery("Find all UCC filings for Acme Corporation in New York");
    console.log(`   Answer length: ${result.answer.length} chars`);
    console.log(`   Sources: ${JSON.stringify(result.sources)}`);
    console.log(`   Tokens used: ${result.tokens_used}`);
    console.log();

    console.log("2. Streaming query:");
    process.stdout.write("   ");
    for await (const chunk of mockStream("What is the risk level for Acme Corporation?")) {
      process.stdout.write(chunk);
    }
    console.log("\n");

    console.log("=== Mock Agent Test Complete ===");
  })();
}
