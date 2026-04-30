/**
 * M21: UCC Agent API Server — Node.js/Express Solution
 * Express application wrapping the UCC research agent.
 *
 * Run with:  node server.js
 * Test with: bash test_api.sh
 */

const express = require("express");
const cors = require("cors");
const { v4: uuidv4 } = require("uuid");
const { QueryRequestSchema, ErrorResponseSchema } = require("./models");
const { mockQuery, mockStream } = require("./mock_agent");

const app = express();
const PORT = 8000;
const VERSION = "1.0.0";
const START_TIME = Date.now();

// ---------------------------------------------------------------------------
// Middleware
// ---------------------------------------------------------------------------

// Parse JSON request bodies
app.use(express.json());

// CORS — allow all origins for development
// In production, replace with specific origins:
//   cors({ origin: ["https://app.yourcompany.com"] })
app.use(cors());

// ---------------------------------------------------------------------------
// GET /health
// ---------------------------------------------------------------------------
app.get("/health", (req, res) => {
  res.json({
    status: "ok",
    version: VERSION,
    uptime_seconds: Math.round((Date.now() - START_TIME) / 1000 * 100) / 100,
    model: "claude-sonnet-4-6",
  });
});

// ---------------------------------------------------------------------------
// POST /query
// ---------------------------------------------------------------------------
app.post("/query", async (req, res) => {
  const requestId = uuidv4();

  // Validate request body
  const parsed = QueryRequestSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({
      error: "validation_error",
      detail: parsed.error.issues.map((i) => i.message).join("; "),
      request_id: requestId,
    });
  }

  const { query } = parsed.data;

  // Reject whitespace-only queries
  if (!query.trim()) {
    return res.status(400).json({
      error: "validation_error",
      detail: "Query must contain non-whitespace characters",
      request_id: requestId,
    });
  }

  try {
    const start = Date.now();
    const result = await mockQuery(query);
    const durationMs = Date.now() - start;

    return res.json({
      answer: result.answer,
      sources: result.sources,
      tokens_used: result.tokens_used,
      duration_ms: durationMs,
      request_id: requestId,
    });
  } catch (err) {
    console.error(`[ERROR] ${requestId}:`, err);
    return res.status(500).json({
      error: "internal_error",
      detail: err.message,
      request_id: requestId,
    });
  }
});

// ---------------------------------------------------------------------------
// POST /query/stream (SSE)
// ---------------------------------------------------------------------------
app.post("/query/stream", async (req, res) => {
  const requestId = uuidv4();

  // Validate request body
  const parsed = QueryRequestSchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({
      error: "validation_error",
      detail: parsed.error.issues.map((i) => i.message).join("; "),
      request_id: requestId,
    });
  }

  const { query } = parsed.data;

  if (!query.trim()) {
    return res.status(400).json({
      error: "validation_error",
      detail: "Query must contain non-whitespace characters",
      request_id: requestId,
    });
  }

  // Set SSE headers
  res.setHeader("Content-Type", "text/event-stream");
  res.setHeader("Cache-Control", "no-cache");
  res.setHeader("Connection", "keep-alive");
  res.setHeader("X-Request-ID", requestId);
  res.flushHeaders();

  try {
    for await (const chunkText of mockStream(query)) {
      const chunk = JSON.stringify({
        chunk: chunkText,
        done: false,
        request_id: requestId,
      });
      res.write(`data: ${chunk}\n\n`);
    }

    // Final chunk
    const finalChunk = JSON.stringify({
      chunk: "",
      done: true,
      request_id: requestId,
    });
    res.write(`data: ${finalChunk}\n\n`);
    res.end();
  } catch (err) {
    console.error(`[ERROR] ${requestId}:`, err);
    const errorChunk = JSON.stringify({
      error: "stream_error",
      detail: err.message,
      request_id: requestId,
    });
    res.write(`data: ${errorChunk}\n\n`);
    res.end();
  }
});

// ---------------------------------------------------------------------------
// Global error handler
// ---------------------------------------------------------------------------
app.use((err, req, res, _next) => {
  const requestId = uuidv4();
  console.error(`[ERROR] ${requestId}:`, err);
  res.status(500).json({
    error: "internal_error",
    detail: err.message,
    request_id: requestId,
  });
});

// ---------------------------------------------------------------------------
// Start server
// ---------------------------------------------------------------------------
app.listen(PORT, () => {
  console.log(`UCC Agent API v${VERSION} running at http://localhost:${PORT}`);
  console.log(`Health: http://localhost:${PORT}/health`);
});
