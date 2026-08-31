import assert from "node:assert/strict";
/**
 * M19 Lab — Structured Logger (Solution)
 * =======================================
 * Complete JSON structured logger with PII scrubbing.
 *
 * Usage:
 *     node structured_logger.js
 */

// =============================================================================
// PII SCRUBBER
// =============================================================================

const PII_PATTERNS = {
  ssn: /\b\d{3}-?\d{2}-?\d{4}\b/g,
  email: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g,
  phone: /(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b/g,
};

const REDACTED = "[REDACTED]";

function scrubPii(data) {
  if (typeof data === "string") {
    let result = data;
    for (const pattern of Object.values(PII_PATTERNS)) {
      pattern.lastIndex = 0;
      result = result.replace(pattern, REDACTED);
    }
    return result;
  } else if (Array.isArray(data)) {
    return data.map((item) => scrubPii(item));
  } else if (data !== null && typeof data === "object") {
    const result = {};
    for (const [k, v] of Object.entries(data)) {
      result[k] = scrubPii(v);
    }
    return result;
  }
  return data;
}

// =============================================================================
// STRUCTURED LOGGER
// =============================================================================

const LEVELS = { DEBUG: 10, INFO: 20, WARN: 30, ERROR: 40 };

class StructuredLogger {
  constructor(serviceName = "agent", minLevel = "DEBUG") {
    this.serviceName = serviceName;
    this.minLevel = minLevel;
    this.logs = [];
  }

  log(level, message, options = {}) {
    if ((LEVELS[level] || 0) < (LEVELS[this.minLevel] || 0)) {
      return null;
    }

    const { traceId, spanId, ...extra } = options;

    let entry = {
      timestamp: new Date().toISOString(),
      level,
      service: this.serviceName,
      message,
      ...(traceId !== undefined && traceId !== null ? { traceId } : {}),
      ...(spanId !== undefined && spanId !== null ? { spanId } : {}),
      ...extra,
    };

    entry = Object.fromEntries(
      Object.entries(entry).filter(([, v]) => v !== null && v !== undefined)
    );

    entry = scrubPii(entry);
    console.log(JSON.stringify(entry));
    this.logs.push(entry);
    return entry;
  }

  logLlmCall({
    model,
    inputTokens,
    outputTokens,
    durationMs,
    traceId,
    spanId,
  }) {
    return this.log("INFO", `LLM call to ${model} completed`, {
      traceId,
      spanId,
      model,
      inputTokens,
      outputTokens,
      totalTokens: inputTokens + outputTokens,
      durationMs,
      eventType: "llm_call",
    });
  }

  logToolCall({
    toolName,
    toolInput,
    toolOutput,
    durationMs,
    traceId,
    spanId,
  }) {
    return this.log("INFO", `Tool '${toolName}' executed`, {
      traceId,
      spanId,
      toolName,
      toolInput: scrubPii(toolInput),
      toolOutput: scrubPii(toolOutput),
      durationMs,
      eventType: "tool_call",
    });
  }

  logError(error, { traceId, spanId, ...extra } = {}) {
    return this.log("ERROR", error.message || String(error), {
      traceId,
      spanId,
      errorType: error.constructor.name,
      eventType: "error",
      ...extra,
    });
  }
}

// =============================================================================
// SELF-TEST
// =============================================================================

function selfTest() {
  console.log("=".repeat(60));
  console.log("M19 Structured Logger \u2014 Self-Test");
  console.log("=".repeat(60));

  console.log("\n--- PII Scrubbing Tests ---\n");

  const testCases = [
    ["SSN in text", "Customer SSN is 123-45-6789, please verify"],
    ["Email in text", "Contact john.doe@example.com for details"],
    ["Phone in text", "Call (555) 123-4567 for support"],
    [
      "Multiple PII",
      "SSN: 987-65-4321, email: jane@test.com, phone: 555-987-6543",
    ],
    [
      "Nested object",
      { name: "John", ssn: "111-22-3333", email: "john@test.com" },
    ],
    ["Array with PII", ["Call 555-111-2222", "Email: test@test.com"]],
    ["No PII", "UCC filing #12345 for Acme Corp in New York"],
  ];

  for (const [label, data] of testCases) {
    const result = scrubPii(data);
    console.log(`  ${label}:`);
    console.log(`    Input:  ${JSON.stringify(data)}`);
    console.log(`    Output: ${JSON.stringify(result)}`);
    console.log();
  }

  console.log("\n--- Structured Logger Tests ---\n");

  let logger = new StructuredLogger("ucc_agent");

  logger.log("INFO", "Agent started", { traceId: "trace_001" });

  logger.logLlmCall({
    model: "claude-sonnet-4-6",
    inputTokens: 350,
    outputTokens: 120,
    durationMs: 823.5,
    traceId: "trace_001",
    spanId: "span_001",
  });

  logger.logToolCall({
    toolName: "search_filings",
    toolInput: { debtor_name: "John Doe", ssn: "123-45-6789" },
    toolOutput: { results: [{ filing: "UCC-001", debtor: "John Doe" }] },
    durationMs: 45.2,
    traceId: "trace_001",
    spanId: "span_002",
  });

  try {
    throw new Error("API rate limit exceeded");
  } catch (e) {
    logger.logError(e, { traceId: "trace_001", spanId: "span_003" });
  }

  logger = new StructuredLogger("ucc_agent", "WARN");
  const result = logger.log("DEBUG", "This should be filtered out");
  assert.ok(
    result === null,
    "DEBUG should be filtered when minLevel is WARN"
  );
  console.log("\n(DEBUG log correctly filtered by minLevel=WARN)");
  console.log("\nAll structured logger tests passed!");
}

export { scrubPii, StructuredLogger, LEVELS };

const isMain =
  process.argv[1] && process.argv[1].endsWith("structured_logger.js");
if (isMain) {
  selfTest();
}
