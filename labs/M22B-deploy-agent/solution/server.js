/**
 * M22B — Express Server for the UCC Agent (Node.js Solution)
 * =============================================================
 * Equivalent of server.py but using Express + SSE for Node.js.
 *
 * Run locally:
 *   npm install
 *   node server.js
 *
 * Endpoints:
 *   GET  /health        — health check
 *   POST /query         — synchronous query
 *   POST /query/stream  — streaming query via SSE
 */

const express = require("express");
const cors = require("cors");

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const PORT = process.env.PORT || 8000;
const ENVIRONMENT = process.env.ENVIRONMENT || "development";
const VERSION = "1.0.0";

// ---------------------------------------------------------------------------
// Mock UCC Filing Data (from M15B)
// ---------------------------------------------------------------------------

const MOCK_FILINGS = [
  {
    filing_number: "UCC-2024-NY-0012847",
    type: "UCC-1",
    state: "New York",
    filing_date: "2024-03-15",
    expiration_date: "2029-03-15",
    status: "Active",
    debtor: {
      name: "Acme Corporation",
      address: "450 West 33rd Street, Suite 800, New York, NY 10001",
    },
    secured_party: {
      name: "Atlantic Capital Partners",
      address: "1 Chase Manhattan Plaza, Floor 45, New York, NY 10005",
    },
    collateral_description:
      "All accounts receivable, inventory, equipment, and general intangibles now owned or hereafter acquired by Debtor.",
  },
  {
    filing_number: "UCC-2024-NY-0015921",
    type: "UCC-1",
    state: "New York",
    filing_date: "2024-05-22",
    expiration_date: "2029-05-22",
    status: "Active",
    debtor: {
      name: "Acme Corporation",
      address: "450 West 33rd Street, Suite 800, New York, NY 10001",
    },
    secured_party: {
      name: "Citibank N.A.",
      address: "388 Greenwich Street, New York, NY 10013",
    },
    collateral_description:
      "All deposit accounts, investment property, and letter-of-credit rights held at or through Citibank.",
  },
  {
    filing_number: "UCC-2024-CA-0101457",
    type: "UCC-1",
    state: "California",
    filing_date: "2024-04-03",
    expiration_date: "2029-04-03",
    status: "Active",
    debtor: {
      name: "Acme Corporation",
      address: "100 California Street, Suite 2000, San Francisco, CA 94111",
    },
    secured_party: {
      name: "Bank of America N.A.",
      address: "555 California Street, San Francisco, CA 94104",
    },
    collateral_description:
      "All equipment and fixtures located at debtor's San Francisco and Los Angeles offices.",
  },
  {
    filing_number: "UCC-2024-TX-0201337",
    type: "UCC-1",
    state: "Texas",
    filing_date: "2024-02-28",
    expiration_date: "2029-02-28",
    status: "Active",
    debtor: {
      name: "Acme Corporation",
      address: "2001 Ross Avenue, Suite 700, Dallas, TX 75201",
    },
    secured_party: {
      name: "PNC Bank N.A.",
      address: "300 Fifth Avenue, Pittsburgh, PA 15222",
    },
    collateral_description:
      "All accounts receivable and contract rights arising from debtor's Texas operations.",
  },
  {
    filing_number: "UCC-2024-FL-0059811",
    type: "UCC-1",
    state: "Florida",
    filing_date: "2024-07-20",
    expiration_date: "2029-07-20",
    status: "Active",
    debtor: {
      name: "Acme Corporation",
      address: "1395 Brickell Avenue, Suite 800, Miami, FL 33131",
    },
    secured_party: {
      name: "Atlantic Capital Partners",
      address: "1 Chase Manhattan Plaza, Floor 45, New York, NY 10005",
    },
    collateral_description:
      "All accounts receivable, inventory, and general intangibles of debtor's Florida division.",
  },
  {
    filing_number: "UCC-2024-IL-0081290",
    type: "UCC-1",
    state: "Illinois",
    filing_date: "2024-04-30",
    expiration_date: "2029-04-30",
    status: "Active",
    debtor: {
      name: "Acme Corporation",
      address: "233 S Wacker Drive, Suite 4500, Chicago, IL 60606",
    },
    secured_party: {
      name: "JPMorgan Chase Bank N.A.",
      address: "383 Madison Avenue, New York, NY 10179",
    },
    collateral_description:
      "All assets of debtor's Illinois subsidiary including accounts, inventory, equipment, and all proceeds thereof.",
  },
  {
    filing_number: "UCC-2024-NY-0019004",
    type: "UCC-1",
    state: "New York",
    filing_date: "2024-08-10",
    expiration_date: "2029-08-10",
    status: "Active",
    debtor: {
      name: "Greenfield Logistics LLC",
      address: "200 Park Avenue, Suite 1500, New York, NY 10166",
    },
    secured_party: {
      name: "JPMorgan Chase Bank N.A.",
      address: "383 Madison Avenue, New York, NY 10179",
    },
    collateral_description:
      "All inventory held at debtor's warehouse facilities in New York State; all accounts receivable arising from distribution operations.",
  },
];

// ---------------------------------------------------------------------------
// Mock Agent Logic
// ---------------------------------------------------------------------------

function searchFilings(debtorName, state, maxResults = 10) {
  let results = MOCK_FILINGS;
  if (debtorName) {
    const lower = debtorName.toLowerCase();
    results = results.filter((f) =>
      f.debtor.name.toLowerCase().includes(lower)
    );
  }
  if (state) {
    const lower = state.toLowerCase();
    results = results.filter((f) => f.state.toLowerCase() === lower);
  }
  return results.slice(0, maxResults);
}

function formatFiling(f) {
  let collateral = f.collateral_description;
  if (collateral.length > 120) collateral = collateral.slice(0, 117) + "...";
  return {
    filing_number: f.filing_number,
    filing_type: f.type,
    state: f.state,
    status: f.status,
    debtor_name: f.debtor.name,
    secured_party_name: f.secured_party.name,
    filing_date: f.filing_date,
    collateral_summary: collateral,
  };
}

function calculateRisk(filings) {
  if (!filings.length) {
    return {
      risk_score: 0,
      risk_level: "Low",
      total_liens: 0,
      states_with_filings: 0,
      recommendation: "No filings found. Low risk by default.",
    };
  }
  const total = filings.length;
  const states = new Set(filings.map((f) => f.state)).size;
  const blanketKeywords = ["all assets", "all accounts", "general intangibles"];
  const blanket = filings.filter((f) =>
    blanketKeywords.some((kw) =>
      f.collateral_description.toLowerCase().includes(kw)
    )
  ).length;

  const score = Math.min(100, 15 + total * 10 + states * 5 + blanket * 8);
  let level, rec;
  if (score >= 75) {
    level = "High";
    rec =
      "Significant lien exposure across multiple jurisdictions. Conduct detailed due diligence before extending credit.";
  } else if (score >= 45) {
    level = "Medium";
    rec =
      "Moderate lien exposure. Review collateral overlap and secured party concentration.";
  } else {
    level = "Low";
    rec = "Limited lien exposure. Standard monitoring recommended.";
  }
  return {
    risk_score: Math.round(score * 10) / 10,
    risk_level: level,
    total_liens: total,
    states_with_filings: states,
    recommendation: rec,
  };
}

function extractDebtor(query) {
  const known = [
    "Acme Corporation",
    "Greenfield Logistics",
    "Lone Star Energy Solutions",
  ];
  const lower = query.toLowerCase();
  for (const name of known) {
    if (lower.includes(name.toLowerCase())) return name;
  }
  if (query.includes(" for ")) {
    const after = query.split(" for ")[1];
    const stopWords = new Set(["in", "from", "at", "with", "on", "and", "or"]);
    const parts = [];
    for (const word of after.split(" ")) {
      const cleaned = word.replace(/[.,;:!?]/g, "");
      if (stopWords.has(cleaned.toLowerCase())) break;
      parts.push(cleaned);
    }
    if (parts.length) return parts.join(" ");
  }
  return null;
}

function extractState(query) {
  const states = {
    "new york": "New York",
    california: "California",
    texas: "Texas",
    florida: "Florida",
    illinois: "Illinois",
  };
  const lower = query.toLowerCase();
  for (const [key, value] of Object.entries(states)) {
    if (lower.includes(key)) return value;
  }
  return null;
}

function mentionsRisk(query) {
  const words = ["risk", "exposure", "assess", "evaluate", "risky"];
  const lower = query.toLowerCase();
  return words.some((w) => lower.includes(w));
}

function buildAnswer(debtorName, filings, state) {
  if (!filings.length) {
    const target = debtorName || "the specified entity";
    const loc = state ? ` in ${state}` : "";
    return `No UCC filings were found for ${target}${loc}.`;
  }
  const debtor = filings[0].debtor.name;
  const statesList = [...new Set(filings.map((f) => f.state))].sort();
  const count = filings.length;
  let answer = `Found ${count} UCC filing(s) for ${debtor}`;
  answer += state
    ? ` in ${state}.`
    : ` across ${statesList.join(", ")}.`;
  answer += "\n";
  for (const f of filings) {
    const col = f.collateral_description.slice(0, 80);
    answer += `\n- ${f.filing_number} (${f.type}, ${f.status}): Filed ${f.filing_date} in ${f.state}. Secured party: ${f.secured_party.name}. Collateral: ${col}...`;
  }
  return answer;
}

// ---------------------------------------------------------------------------
// Express App
// ---------------------------------------------------------------------------

const app = express();
app.use(cors());
app.use(express.json());

// GET /health
app.get("/health", (req, res) => {
  res.json({
    status: "healthy",
    version: VERSION,
    environment: ENVIRONMENT,
    mock_mode: true,
    timestamp: new Date().toISOString(),
  });
});

// POST /query
app.post("/query", (req, res) => {
  try {
    const start = Date.now();
    const { query, state, include_risk = false, max_results = 10 } = req.body;

    if (!query || query.length < 1) {
      return res.status(422).json({
        error: "Validation Error",
        detail: "query field is required and must not be empty",
        status_code: 422,
        timestamp: new Date().toISOString(),
      });
    }

    const debtorName = extractDebtor(query);
    const extractedState = state || extractState(query);
    const filings = searchFilings(debtorName, extractedState, max_results);
    const filingSummaries = filings.map(formatFiling);
    const answer = buildAnswer(debtorName, filings, extractedState);

    let risk = null;
    if (include_risk || mentionsRisk(query)) {
      risk = calculateRisk(filings);
    }

    const elapsed = Date.now() - start;

    res.json({
      query,
      answer,
      filings: filingSummaries,
      risk,
      processing_time_ms: elapsed,
      timestamp: new Date().toISOString(),
      mock_mode: true,
    });
  } catch (err) {
    res.status(500).json({
      error: "Internal Server Error",
      detail: err.message,
      status_code: 500,
      timestamp: new Date().toISOString(),
    });
  }
});

// POST /query/stream (Server-Sent Events)
app.post("/query/stream", (req, res) => {
  const { query, state, include_risk = false, max_results = 10 } = req.body;

  if (!query) {
    return res.status(422).json({
      error: "Validation Error",
      detail: "query field is required",
      status_code: 422,
    });
  }

  res.writeHead(200, {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    Connection: "keep-alive",
    "X-Accel-Buffering": "no",
  });

  const debtorName = extractDebtor(query);
  const extractedState = state || extractState(query);
  const filings = searchFilings(debtorName, extractedState, max_results);
  const answer = buildAnswer(debtorName, filings, extractedState);

  // Stream answer in chunks
  const words = answer.split(" ");
  const chunkSize = 5;
  let i = 0;

  function sendNextChunk() {
    if (i < words.length) {
      const chunk = words.slice(i, i + chunkSize).join(" ");
      res.write(`event: chunk\ndata: ${JSON.stringify({ text: chunk })}\n\n`);
      i += chunkSize;
      setTimeout(sendNextChunk, 50);
    } else {
      // Send filing summaries
      for (const f of filings) {
        res.write(
          `event: filing\ndata: ${JSON.stringify(formatFiling(f))}\n\n`
        );
      }

      // Send risk if requested
      if (include_risk || mentionsRisk(query)) {
        const risk = calculateRisk(filings);
        res.write(`event: risk\ndata: ${JSON.stringify(risk)}\n\n`);
      }

      // Done
      res.write(
        `event: done\ndata: ${JSON.stringify({ status: "complete" })}\n\n`
      );
      res.end();
    }
  }

  sendNextChunk();
});

// ---------------------------------------------------------------------------
// Start server
// ---------------------------------------------------------------------------

app.listen(PORT, "0.0.0.0", () => {
  console.log(`UCC Agent API (Node.js) running on http://0.0.0.0:${PORT}`);
  console.log(`  Health: http://localhost:${PORT}/health`);
  console.log(`  Docs:   http://localhost:${PORT}/query`);
  console.log(`  Environment: ${ENVIRONMENT}`);
});

module.exports = app;
