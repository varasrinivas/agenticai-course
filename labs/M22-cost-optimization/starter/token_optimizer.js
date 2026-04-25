/**
 * M22 Lab — Token Optimizer (Starter)
 * ====================================
 * Compress system prompts, limit output tokens, and trim conversation
 * history to reduce the number of tokens sent with every API call.
 *
 * KEY CONCEPT: Tokens are the unit of cost. Every word in your system
 * prompt is re-sent on EVERY call. A 2000-token system prompt across
 * 1000 daily calls = 2M extra input tokens/day. Compressing that prompt
 * by 30% saves 600K tokens/day — real money at scale.
 *
 * Usage:
 *     node token_optimizer.js
 */

class TokenOptimizer {
  /**
   * @param {number} maxMessages - Max messages to keep in sliding window
   */
  constructor(maxMessages = 10) {
    this.maxMessages = maxMessages;
    this.stats = { originalTokens: 0, optimizedTokens: 0 };

    this.compressionRules = [
      [/You are an AI assistant that /gi, ""],
      [/Please ensure that you /gi, ""],
      [/It is important that you /gi, ""],
      [/Make sure to always /gi, "Always "],
      [/You should always /gi, "Always "],
      [/You must always /gi, "Always "],
      [/Please provide /gi, "Provide "],
      [/Please respond /gi, "Respond "],
      [/Please make sure /gi, "Ensure "],
      [/in order to /gi, "to "],
      [/due to the fact that /gi, "because "],
      [/for the purpose of /gi, "for "],
      [/in the event that /gi, "if "],
      [/at this point in time /gi, "now "],
      [/on a regular basis /gi, "regularly "],
      [/a large number of /gi, "many "],
      [/in a timely manner /gi, "promptly "],
      [/take into consideration /gi, "consider "],
      [/with regard to /gi, "regarding "],
      [/in addition to /gi, "besides "],
      [/prior to /gi, "before "],
      [/subsequent to /gi, "after "],
      [/in the absence of /gi, "without "],
      [/is able to /gi, "can "],
      [/has the ability to /gi, "can "],
    ];
  }

  /**
   * Rough token count: ~4 chars per token for English text.
   * @param {string} text
   * @returns {number}
   */
  estimateTokens(text) {
    // TODO: return Math.max(1, Math.ceil(text.length / 4)) or 0 if empty
  }

  /**
   * Compress a system prompt by removing filler phrases and whitespace.
   * @param {string} prompt
   * @returns {object} { original, compressed, originalTokens, compressedTokens, reductionPct }
   */
  compressSystemPrompt(prompt) {
    // TODO: Implement prompt compression
    // 1. Apply each compression rule
    // 2. Collapse multiple spaces
    // 3. Collapse multiple newlines
    // 4. Trim each line
    // 5. Calculate tokens and reduction percentage
    // 6. Update this.stats
  }

  /**
   * Generate output constraint instructions.
   * @param {number} maxTokens
   * @param {string|null} formatHint - "json", "brief", "bullet_points"
   * @returns {object} { constraintText, estimatedTokens }
   */
  setOutputConstraints(maxTokens = 500, formatHint = null) {
    // TODO: Build constraint instruction string
  }

  /**
   * Apply sliding window to conversation messages.
   * @param {Array<{role: string, content: string}>} messages
   * @returns {object} { originalMessages, optimizedMessages, originalCount, optimizedCount, tokensSaved }
   */
  optimizeMessages(messages) {
    // TODO: Keep first message + last (maxMessages - 1) messages
  }

  /**
   * Return cumulative savings stats.
   * @returns {object} { originalTokens, optimizedTokens, savedTokens, reductionPct }
   */
  getSavings() {
    // TODO: Calculate from this.stats
  }
}

// =============================================================================
// SELF-TEST
// =============================================================================

function selfTest() {
  console.log("=".repeat(60));
  console.log("M22 Lab — Token Optimizer Self-Test");
  console.log("=".repeat(60));

  const optimizer = new TokenOptimizer(6);

  // --- Test 1: System prompt compression ---
  console.log("\n--- Test 1: System Prompt Compression ---");
  const samplePrompt = `You are an AI assistant that specializes in UCC filing research.
You should always provide accurate information about Uniform Commercial Code filings.
Please ensure that you check all relevant databases prior to responding.
It is important that you identify the secured party, debtor, and collateral
in each filing. Make sure to always include the filing number and jurisdiction.
Please provide responses in a clear, structured format.
In order to help the user, you must always cross-reference entity names
due to the fact that companies sometimes file under different names.
For the purpose of risk assessment, take into consideration the filing
date, the collateral type, and whether the filing has been amended
subsequent to the original filing. In the event that a filing
has the ability to be matched to multiple entities, please make sure
to list all possible matches with regard to the debtor name.
You are an AI assistant that is able to handle complex UCC queries
on a regular basis in a timely manner. Please respond with
a large number of relevant details in addition to the filing summary.
In the absence of matching filings, please provide a clear explanation
at this point in time for why no results were found.`;

  const result = optimizer.compressSystemPrompt(samplePrompt);
  console.log(`  Original:   ${result.originalTokens} tokens (${result.original.length} chars)`);
  console.log(`  Compressed: ${result.compressedTokens} tokens (${result.compressed.length} chars)`);
  console.log(`  Reduction:  ${result.reductionPct.toFixed(1)}%`);
  console.assert(result.reductionPct >= 25, `FAIL: Expected >= 25% reduction`);
  console.log(`  PASS: Achieved ${result.reductionPct.toFixed(1)}% reduction`);

  // --- Test 2: Output constraints ---
  console.log("\n--- Test 2: Output Constraints ---");
  const constraints = optimizer.setOutputConstraints(300, "json");
  console.log(`  Constraint text: "${constraints.constraintText}"`);
  console.assert(constraints.constraintText.toLowerCase().includes("json"));
  console.log("  PASS: JSON format constraint applied");

  const constraints2 = optimizer.setOutputConstraints(200, "brief");
  console.log(`  Brief constraint: "${constraints2.constraintText}"`);
  console.log("  PASS: Brief format constraint applied");

  // --- Test 3: Message windowing ---
  console.log("\n--- Test 3: Message Windowing ---");
  const messages = [
    { role: "user", content: "I need help with UCC filings research for our portfolio." },
    { role: "assistant", content: "I'd be happy to help. What would you like to know?" },
    { role: "user", content: "First, find all filings for Acme Corp in New York." },
    { role: "assistant", content: "I found 3 UCC filings for Acme Corp in New York..." },
    { role: "user", content: "Now check Texas as well." },
    { role: "assistant", content: "I found 2 additional filings in Texas..." },
    { role: "user", content: "Can you resolve whether Acme Corp and ACME Corporation are the same?" },
    { role: "assistant", content: "They appear to be the same entity..." },
    { role: "user", content: "What's the total risk exposure?" },
    { role: "assistant", content: "The total risk exposure is approximately $2.4M..." },
    { role: "user", content: "Generate a summary report." },
    { role: "assistant", content: "Here is the portfolio summary report..." },
  ];

  const msgResult = optimizer.optimizeMessages(messages);
  console.log(`  Original messages:  ${msgResult.originalCount}`);
  console.log(`  Optimized messages: ${msgResult.optimizedCount}`);
  console.log(`  Tokens saved:       ~${msgResult.tokensSaved}`);
  console.assert(msgResult.optimizedCount <= 6, "FAIL: Should have trimmed");
  console.assert(
    msgResult.optimizedMessages[0].content === messages[0].content,
    "FAIL: First message should be preserved"
  );
  console.log(`  PASS: Message window applied`);

  // --- Test 4: Cumulative savings ---
  console.log("\n--- Test 4: Cumulative Savings ---");
  const savings = optimizer.getSavings();
  console.log(`  Total original tokens:  ${savings.originalTokens}`);
  console.log(`  Total optimized tokens: ${savings.optimizedTokens}`);
  console.log(`  Total saved:            ${savings.savedTokens}`);
  console.log(`  Overall reduction:      ${savings.reductionPct.toFixed(1)}%`);
  console.assert(savings.reductionPct > 0, "FAIL: Should show savings");
  console.log("  PASS: Cumulative tracking works");

  console.log("\n" + "=".repeat(60));
  console.log("All token optimizer tests passed!");
  console.log("=".repeat(60));
}

selfTest();

module.exports = { TokenOptimizer };
