/**
 * M02 Lab — Step 1: Token Counter (Node.js Solution)
 * =====================================================
 * Count tokens in different text types to understand tokenization.
 *
 * Uses a character-based approximation (~4 chars per token for English).
 * For exact counts, install `gpt-tokenizer` and use encode().
 */

const SAMPLE_TEXTS = {
  "Short sentence": "The quick brown fox jumps over the lazy dog.",
  "Paragraph":
    "Uniform Commercial Code filings, commonly known as UCC filings, " +
    "are legal forms that creditors file to establish their interest in " +
    "a debtor's personal property or assets used as collateral for a loan. " +
    "These filings serve as public notice that a lender has a security " +
    "interest in the specified assets, which helps establish priority " +
    "among creditors in case of default or bankruptcy.",
  "Code snippet": `def search_filings(debtor_name: str) -> list[dict]:
    """Search UCC filings by debtor name."""
    results = []
    for filing in ALL_FILINGS:
        if debtor_name.lower() in filing["debtor"]["name"].lower():
            results.append(filing)
    return results`,
  "JSON blob":
    '{"filing_number":"UCC-2024-NY-0012847","type":"UCC-1","state":"New York","debtor":{"name":"Greenfield Logistics LLC","org_type":"LLC"},"status":"Active"}',
};

/**
 * Count tokens using a character-based approximation.
 * English prose averages ~4 characters per token; code and structured
 * data average ~2-3 characters per token.
 *
 * This uses a regex split that breaks on word boundaries, punctuation,
 * and special characters — similar to how real BPE tokenizers work.
 *
 * @param {string} text - The text to tokenize
 * @returns {number} Approximate token count
 */
function countTokens(text) {
  // Split on whitespace and individual punctuation/special characters
  // This approximates BPE tokenization for demonstration purposes
  const tokens = text.match(/\w+|[^\s\w]/g);
  return tokens ? tokens.length : 0;
}

// ─── Main ───────────────────────────────────────────────────────────────────

console.log("=== Token Counter ===\n");

const header = `${"Text Type".padEnd(20)} | ${"Characters".padStart(10)} | ${"Tokens".padStart(6)} | ${"Ratio".padStart(5)}`;
console.log(header);
console.log(
  "-".repeat(20) +
    "-|-" +
    "-".repeat(10) +
    "-|-" +
    "-".repeat(6) +
    "-|-" +
    "-".repeat(5)
);

for (const [name, text] of Object.entries(SAMPLE_TEXTS)) {
  try {
    const tokens = countTokens(text);
    const ratio = tokens > 0 ? (text.length / tokens).toFixed(1) : "N/A";
    console.log(
      `${name.padEnd(20)} | ${String(text.length).padStart(10)} | ${String(tokens).padStart(6)} | ${String(ratio).padStart(5)}`
    );
  } catch (e) {
    console.log(`${name.padEnd(20)} | [ERROR] ${e.message}`);
  }
}

console.log(
  "\nKey insight: Code and structured data use MORE tokens per character than prose."
);
