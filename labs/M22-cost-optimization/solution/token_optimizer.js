const assert = require("node:assert/strict");
/**
 * M22 Lab — Token Optimizer (Solution)
 * ======================================
 * Complete token optimizer with prompt compression, message windowing,
 * and output constraints.
 *
 * Usage:
 *     node token_optimizer.js
 */

class TokenOptimizer {
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

  estimateTokens(text) {
    if (!text) return 0;
    return Math.max(1, Math.ceil(text.length / 4));
  }

  compressSystemPrompt(prompt) {
    const original = prompt;
    let compressed = prompt;

    for (const [pattern, replacement] of this.compressionRules) {
      compressed = compressed.replace(pattern, replacement);
    }

    compressed = compressed.replace(/ {2,}/g, " ");
    compressed = compressed.replace(/\n{3,}/g, "\n\n");
    compressed = compressed
      .split("\n")
      .map((line) => line.trim())
      .join("\n")
      .trim();

    const originalTokens = this.estimateTokens(original);
    const compressedTokens = this.estimateTokens(compressed);

    this.stats.originalTokens += originalTokens;
    this.stats.optimizedTokens += compressedTokens;

    const reductionPct =
      originalTokens > 0
        ? ((originalTokens - compressedTokens) / originalTokens) * 100
        : 0;

    return { original, compressed, originalTokens, compressedTokens, reductionPct };
  }

  setOutputConstraints(maxTokens = 500, formatHint = null) {
    const parts = [`Respond concisely. Max length: ~${maxTokens} tokens.`];
    if (formatHint === "json") parts.push("Return valid JSON only.");
    else if (formatHint === "brief") parts.push("Use 2-3 sentences maximum.");
    else if (formatHint === "bullet_points") parts.push("Use bullet points, no prose.");

    const constraintText = parts.join(" ");
    return { constraintText, estimatedTokens: this.estimateTokens(constraintText) };
  }

  optimizeMessages(messages) {
    const originalCount = messages.length;
    const originalTokens = messages.reduce(
      (sum, m) => sum + this.estimateTokens(m.content || ""),
      0
    );

    let optimized;
    if (messages.length <= this.maxMessages) {
      optimized = [...messages];
    } else {
      optimized = [messages[0], ...messages.slice(-(this.maxMessages - 1))];
    }

    const optimizedTokens = optimized.reduce(
      (sum, m) => sum + this.estimateTokens(m.content || ""),
      0
    );
    const tokensSaved = originalTokens - optimizedTokens;

    this.stats.originalTokens += originalTokens;
    this.stats.optimizedTokens += optimizedTokens;

    return {
      originalMessages: messages,
      optimizedMessages: optimized,
      originalCount,
      optimizedCount: optimized.length,
      tokensSaved,
    };
  }

  getSavings() {
    const saved = this.stats.originalTokens - this.stats.optimizedTokens;
    const reductionPct =
      this.stats.originalTokens > 0
        ? (saved / this.stats.originalTokens) * 100
        : 0;
    return {
      originalTokens: this.stats.originalTokens,
      optimizedTokens: this.stats.optimizedTokens,
      savedTokens: saved,
      reductionPct,
    };
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
  console.log(`  Original:   ${result.originalTokens} tokens`);
  console.log(`  Compressed: ${result.compressedTokens} tokens`);
  console.log(`  Reduction:  ${result.reductionPct.toFixed(1)}%`);
  assert.ok(result.reductionPct >= 25, "FAIL: Expected >= 25%");
  console.log(`  PASS: Achieved ${result.reductionPct.toFixed(1)}% reduction`);

  console.log("\n--- Test 2: Output Constraints ---");
  const c1 = optimizer.setOutputConstraints(300, "json");
  console.log(`  JSON: "${c1.constraintText}"`);
  assert.ok(c1.constraintText.toLowerCase().includes("json"));
  console.log("  PASS");

  console.log("\n--- Test 3: Message Windowing ---");
  const messages = Array.from({ length: 12 }, (_, i) => ({
    role: i % 2 === 0 ? "user" : "assistant",
    content: `Message ${i + 1} content here.`,
  }));
  const msgResult = optimizer.optimizeMessages(messages);
  console.log(`  ${msgResult.originalCount} -> ${msgResult.optimizedCount} messages`);
  assert.ok(msgResult.optimizedCount <= 6);
  console.log("  PASS");

  console.log("\n--- Test 4: Cumulative Savings ---");
  const savings = optimizer.getSavings();
  console.log(`  Saved: ${savings.savedTokens} tokens (${savings.reductionPct.toFixed(1)}%)`);
  assert.ok(savings.reductionPct > 0);
  console.log("  PASS");

  console.log("\n" + "=".repeat(60));
  console.log("All token optimizer tests passed!");
  console.log("=".repeat(60));
}

selfTest();

export { TokenOptimizer };
