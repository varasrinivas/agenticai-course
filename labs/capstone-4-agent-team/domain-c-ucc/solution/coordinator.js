/**
 * Pipeline Coordinator — UCC Data Engineering Multi-Agent Pipeline (Node.js Solution)
 *
 * Self-contained Node.js implementation of the 4-agent pipeline coordinator
 * with circuit breaker and HITL simulation.
 */

import Anthropic from "@anthropic-ai/sdk";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------
const MODEL = "claude-sonnet-4-20250514";
const MAX_ITERATIONS = 10;
const QUALITY_SCORE_THRESHOLD = 80.0;

// ---------------------------------------------------------------------------
// Mock Data (subset for self-contained JS)
// ---------------------------------------------------------------------------
const FILING_BATCHES = {
  "BATCH-001": {
    batch_id: "BATCH-001",
    source: "secretary_of_state_CA",
    format: "csv",
    filing_count: 5,
    filings: [
      { filing_number: "UCC-2024-CA-00101", debtor_name: "ACME CORP", secured_party: "First National Bank", collateral: "All inventory and equipment", filing_date: "2024-01-15", status: "active", debtor_ein: "12-3456789" },
      { filing_number: "UCC-2024-CA-00102", debtor_name: "Acme Corporation", secured_party: "First National Bank", collateral: "Accounts receivable", filing_date: "2024-02-20", status: "active", debtor_ein: "12-3456789" },
      { filing_number: "UCC-2024-CA-00103", debtor_name: "PACIFIC COAST BUILDERS INC", secured_party: "Western Credit Union", collateral: "Construction equipment, vehicles", filing_date: "2024-03-10", status: "active", debtor_ein: "98-7654321" },
      { filing_number: "UCC-2024-CA-00104", debtor_name: "SMITH & JONES LLC", secured_party: "Community Bank", collateral: "All assets", filing_date: "2024-04-05", status: "terminated", debtor_ein: "55-1234567" },
      { filing_number: "UCC-2024-CA-00105", debtor_name: "ACME CORP DBA ACME WIDGETS", secured_party: "Second Regional Bank", collateral: "Intellectual property and patents", filing_date: "2024-05-01", status: "active", debtor_ein: "12-3456789" },
    ],
  },
  "BATCH-009": {
    batch_id: "BATCH-009",
    source: "secretary_of_state_NV",
    format: "xlsx",
    filing_count: 1,
    filings: [
      { filing_number: "UCC-2024-NV-00901", debtor_name: "DESERT SOLAR LLC", secured_party: "Green Energy Fund", collateral: "Solar panels", filing_date: "2024-06-01", status: "active" },
    ],
  },
};

const ENTITY_REGISTRY = {
  "ENT-001": { entity_id: "ENT-001", canonical_name: "ACME CORPORATION", aliases: ["ACME CORP", "ACME CORP DBA ACME WIDGETS", "Acme Corporation"], ein: "12-3456789", risk_tier: "medium" },
  "ENT-002": { entity_id: "ENT-002", canonical_name: "PACIFIC COAST BUILDERS INC", aliases: ["PACIFIC COAST BUILDERS INC"], ein: "98-7654321", risk_tier: "low" },
};

const COLLATERAL_TYPES = {
  inventory: ["inventory", "stock", "goods"],
  equipment: ["equipment", "machinery", "vehicles", "construction equipment"],
  receivables: ["accounts receivable", "receivables"],
  intellectual_property: ["intellectual property", "patents", "IP"],
  general_intangibles: ["all assets", "general intangibles"],
};

const SUPPORTED_FORMATS = ["csv", "json", "xml"];

// ---------------------------------------------------------------------------
// Circuit Breaker
// ---------------------------------------------------------------------------
class CircuitBreaker {
  constructor(name, threshold = 0.1, windowSize = 20, cooldownMs = 60000) {
    this.name = name;
    this.threshold = threshold;
    this.windowSize = windowSize;
    this.cooldownMs = cooldownMs;
    this.results = [];
    this.state = "closed";
    this.lastFailureTime = null;
  }

  get failureRate() {
    if (this.results.length === 0) return 0;
    const failures = this.results.filter((r) => !r).length;
    return failures / this.results.length;
  }

  recordSuccess() {
    this.results.push(true);
    if (this.results.length > this.windowSize) this.results.shift();
    if (this.state === "half_open") this.state = "closed";
  }

  recordFailure() {
    this.results.push(false);
    if (this.results.length > this.windowSize) this.results.shift();
    this.lastFailureTime = Date.now();
    if (this.failureRate > this.threshold && this.results.length >= 3) {
      this.state = "open";
      console.log(
        `  [CIRCUIT BREAKER] TRIPPED! Rate: ${(this.failureRate * 100).toFixed(1)}%`
      );
    }
  }

  isTripped() {
    if (this.state === "closed") return false;
    if (this.state === "open") {
      if (this.lastFailureTime && Date.now() - this.lastFailureTime >= this.cooldownMs) {
        this.state = "half_open";
        return false;
      }
      return true;
    }
    return false;
  }

  reset() {
    this.results = [];
    this.state = "closed";
    this.lastFailureTime = null;
  }
}

// ---------------------------------------------------------------------------
// Tool Implementations
// ---------------------------------------------------------------------------
function detectFormat(batchId) {
  const batch = FILING_BATCHES[batchId];
  if (!batch) return { error: `Batch ${batchId} not found` };
  return {
    batch_id: batchId,
    format: batch.format,
    supported: SUPPORTED_FORMATS.includes(batch.format),
    source: batch.source,
    filing_count: batch.filing_count,
  };
}

function parseBatch(batchId) {
  const batch = FILING_BATCHES[batchId];
  if (!batch) return { error: `Batch ${batchId} not found` };
  if (!SUPPORTED_FORMATS.includes(batch.format)) {
    return { error: `Unsupported format: ${batch.format}`, batch_id: batchId, parse_error: true };
  }
  let errorCount = 0;
  for (const f of batch.filings) {
    if (!f.filing_number || !f.debtor_name) errorCount++;
  }
  return { batch_id: batchId, filing_count: batch.filings.length, filings: batch.filings, parse_error_count: errorCount };
}

function resolveEntities(filings) {
  const resolutions = [];
  for (const f of filings) {
    let matched = null;
    let method = "unresolved";
    let confidence = 0.0;

    // EIN match
    if (f.debtor_ein) {
      for (const [eid, erec] of Object.entries(ENTITY_REGISTRY)) {
        if (erec.ein === f.debtor_ein) {
          matched = erec;
          method = "ein";
          confidence = 1.0;
          break;
        }
      }
    }
    // Alias match
    if (!matched) {
      for (const [eid, erec] of Object.entries(ENTITY_REGISTRY)) {
        if (erec.aliases.includes(f.debtor_name)) {
          matched = erec;
          method = "alias";
          confidence = 0.9;
          break;
        }
      }
    }

    resolutions.push({
      filing_number: f.filing_number,
      debtor_name: f.debtor_name,
      canonical_name: matched ? matched.canonical_name : null,
      confidence,
      match_method: method,
    });
  }
  return resolutions;
}

function classifyCollateral(filings) {
  const results = [];
  for (const f of filings) {
    const text = (f.collateral || "").toLowerCase();
    const categories = [];
    for (const [cat, keywords] of Object.entries(COLLATERAL_TYPES)) {
      if (keywords.some((kw) => text.includes(kw.toLowerCase()))) {
        categories.push(cat);
      }
    }
    results.push({ ...f, collateral_categories: categories.length > 0 ? categories : ["unclassified"] });
  }
  return results;
}

function runQualityChecks(filings) {
  let passed = 0;
  let failed = 0;
  const failures = [];
  for (const f of filings) {
    if (f.filing_number) passed++;
    else { failed++; failures.push({ rule: "filing_number_required", filing: f.filing_number }); }
    if (f.debtor_name) passed++;
    else { failed++; failures.push({ rule: "debtor_name_required", filing: f.filing_number }); }
    if (/^\d{4}-\d{2}-\d{2}$/.test(f.filing_date)) passed++;
    else { failed++; failures.push({ rule: "valid_date_format", filing: f.filing_number }); }
  }
  const total = passed + failed;
  const score = total > 0 ? (passed / total) * 100 : 0;
  return { checks_passed: passed, checks_failed: failed, total_checks: total, quality_score: score, failures };
}

// ---------------------------------------------------------------------------
// Pipeline Coordinator
// ---------------------------------------------------------------------------
async function runPipeline(batchId) {
  const batch = FILING_BATCHES[batchId];
  if (!batch) {
    console.log(`[ERROR] Batch ${batchId} not found`);
    return { halted: true, reason: "Not found" };
  }

  console.log(`\n${"#".repeat(60)}`);
  console.log(`# Pipeline for ${batchId} -- ${batch.source}`);
  console.log(`# Format: ${batch.format} | Filings: ${batch.filing_count}`);
  console.log(`${"#".repeat(60)}`);

  // Step 1: Ingestion
  const format = detectFormat(batchId);
  console.log(`\n[IngestionAgent] Format: ${format.format} (supported: ${format.supported})`);

  if (!format.supported) {
    console.log(`  [HALTED] Unsupported format: ${format.format}`);
    return { halted: true, reason: `Unsupported format: ${format.format}` };
  }

  const parsed = parseBatch(batchId);
  console.log(`[IngestionAgent] Parsed ${parsed.filing_count} filings (errors: ${parsed.parse_error_count})`);

  // Step 2: Transformation
  const classified = classifyCollateral(parsed.filings);
  const resolutions = resolveEntities(parsed.filings);
  const resolved = resolutions.filter((r) => r.confidence > 0).length;
  const unresolved = resolutions.filter((r) => r.confidence === 0).length;
  console.log(`[TransformationAgent] Resolved: ${resolved}, Unresolved: ${unresolved}`);

  // Step 3: Quality
  const quality = runQualityChecks(parsed.filings);
  console.log(`[QualityAgent] Score: ${quality.quality_score.toFixed(1)}% (${quality.checks_passed}/${quality.total_checks} passed)`);

  // HITL check
  let hitlTriggered = false;
  if (quality.quality_score < QUALITY_SCORE_THRESHOLD) {
    console.log(`\n  *** HITL TRIGGERED (score ${quality.quality_score.toFixed(1)}% < ${QUALITY_SCORE_THRESHOLD}%) ***`);
    hitlTriggered = true;
    console.log(`  Auto-approving for demo purposes.`);
  }

  // Step 4: Reporting
  const activeCount = parsed.filings.filter((f) => f.status === "active").length;
  const terminatedCount = parsed.filings.filter((f) => f.status === "terminated").length;
  console.log(`[ReportingAgent] Active liens: ${activeCount}, Terminated: ${terminatedCount}`);
  console.log(`[ReportingAgent] Report generated.`);

  console.log(`\n${"*".repeat(60)}`);
  console.log(`Pipeline COMPLETE: ${batchId}`);
  console.log(`  Quality: ${quality.quality_score.toFixed(1)}%`);
  console.log(`  Entities resolved: ${resolved}`);
  console.log(`  HITL triggered: ${hitlTriggered}`);
  console.log(`${"*".repeat(60)}`);

  return {
    completed: true,
    quality_score: quality.quality_score,
    entities_resolved: resolved,
    hitlTriggered,
  };
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
async function main() {
  const breaker = new CircuitBreaker("parse_errors");

  console.log("=== TEST 1: Happy Path (BATCH-001) ===");
  breaker.reset();
  await runPipeline("BATCH-001");

  console.log("\n=== TEST 2: Unsupported Format (BATCH-009) ===");
  breaker.reset();
  const result = await runPipeline("BATCH-009");
  if (result.halted) {
    breaker.recordFailure();
    console.log(`  Circuit breaker state: ${breaker.state}`);
  }

  console.log("\n=== TEST 3: Circuit Breaker Batch ===");
  breaker.reset();
  const batchIds = ["BATCH-009", "BATCH-009", "BATCH-009", "BATCH-001"];
  for (const bid of batchIds) {
    if (breaker.isTripped()) {
      console.log(`\n[${bid}] BLOCKED -- circuit breaker is ${breaker.state}`);
      continue;
    }
    const r = await runPipeline(bid);
    if (r.halted) {
      breaker.recordFailure();
    } else {
      breaker.recordSuccess();
    }
  }
  console.log(`\nFinal circuit breaker state: ${breaker.state}`);
}

main().catch(console.error);
