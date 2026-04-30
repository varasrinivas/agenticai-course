/**
 * M21: API Request/Response Models — Node.js Solution
 * Zod schemas for validating request/response payloads.
 *
 * Zod is the Node.js equivalent of Pydantic — runtime type validation
 * with automatic TypeScript type inference.
 */

const { z } = require("zod");

// ---------------------------------------------------------------------------
// Request Models
// ---------------------------------------------------------------------------

const QueryRequestSchema = z.object({
  query: z
    .string()
    .min(1, "Query must not be empty")
    .describe("The user's natural-language question about UCC filings"),
  session_id: z
    .string()
    .optional()
    .nullable()
    .describe("Optional session ID for conversation continuity"),
  stream: z
    .boolean()
    .default(false)
    .describe("Whether to use SSE streaming response"),
});

// ---------------------------------------------------------------------------
// Response Models
// ---------------------------------------------------------------------------

const QueryResponseSchema = z.object({
  answer: z.string().describe("The agent's natural-language response"),
  sources: z
    .array(z.string())
    .describe("List of filing numbers or references used"),
  tokens_used: z
    .number()
    .int()
    .describe("Number of tokens consumed by the request"),
  duration_ms: z
    .number()
    .describe("Request processing time in milliseconds"),
  request_id: z.string().describe("Unique request ID for tracing"),
});

const HealthResponseSchema = z.object({
  status: z.string().describe("Server status: 'ok' or 'degraded'"),
  version: z.string().describe("API version string"),
  uptime_seconds: z.number().describe("Seconds since server started"),
  model: z.string().describe("Claude model the agent uses"),
});

const StreamChunkSchema = z.object({
  chunk: z.string().describe("One piece of the streamed response text"),
  done: z.boolean().default(false).describe("True for the final chunk"),
  request_id: z
    .string()
    .describe("Same UUID across all chunks in one stream"),
});

const ErrorResponseSchema = z.object({
  error: z
    .string()
    .describe("Short error description, e.g. 'validation_error'"),
  detail: z
    .string()
    .optional()
    .nullable()
    .describe("Longer explanation of what went wrong"),
  request_id: z.string().describe("UUID for tracing, even on errors"),
});

// ---------------------------------------------------------------------------
// Exports
// ---------------------------------------------------------------------------
module.exports = {
  QueryRequestSchema,
  QueryResponseSchema,
  HealthResponseSchema,
  StreamChunkSchema,
  ErrorResponseSchema,
};

// ---------------------------------------------------------------------------
// Self-test
// ---------------------------------------------------------------------------
if (require.main === module) {
  console.log("=== Testing Zod Models ===\n");

  // Test QueryRequest
  try {
    const req = QueryRequestSchema.parse({
      query: "Find UCC filings for Acme Corp",
    });
    console.log(`[PASS] QueryRequest: ${JSON.stringify(req)}`);
  } catch (e) {
    console.log(`[FAIL] QueryRequest: ${e.message}`);
  }

  // Test QueryRequest rejects empty query
  try {
    QueryRequestSchema.parse({ query: "" });
    console.log("[FAIL] QueryRequest should reject empty query");
  } catch (e) {
    console.log("[PASS] QueryRequest correctly rejects empty query");
  }

  // Test QueryResponse
  try {
    const resp = QueryResponseSchema.parse({
      answer: "Found 3 filings for Acme Corp in New York.",
      sources: ["UCC-2024-NY-0012847", "UCC-2024-NY-0012848"],
      tokens_used: 1250,
      duration_ms: 1823.5,
      request_id: "abc-123-def",
    });
    console.log(`[PASS] QueryResponse: ${JSON.stringify(resp)}`);
  } catch (e) {
    console.log(`[FAIL] QueryResponse: ${e.message}`);
  }

  // Test HealthResponse
  try {
    const health = HealthResponseSchema.parse({
      status: "ok",
      version: "1.0.0",
      uptime_seconds: 3661.2,
      model: "claude-sonnet-4-6",
    });
    console.log(`[PASS] HealthResponse: ${JSON.stringify(health)}`);
  } catch (e) {
    console.log(`[FAIL] HealthResponse: ${e.message}`);
  }

  // Test StreamChunk
  try {
    const chunk = StreamChunkSchema.parse({
      chunk: "Based on",
      done: false,
      request_id: "abc-123",
    });
    console.log(`[PASS] StreamChunk: ${JSON.stringify(chunk)}`);
  } catch (e) {
    console.log(`[FAIL] StreamChunk: ${e.message}`);
  }

  // Test ErrorResponse
  try {
    const err = ErrorResponseSchema.parse({
      error: "validation_error",
      detail: "Query must not be empty",
      request_id: "abc-123",
    });
    console.log(`[PASS] ErrorResponse: ${JSON.stringify(err)}`);
  } catch (e) {
    console.log(`[FAIL] ErrorResponse: ${e.message}`);
  }

  console.log("\n=== Model Tests Complete ===");
}
