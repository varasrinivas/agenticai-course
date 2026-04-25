/**
 * M26 Lab — Step 4: Coordinator + Subagent Pattern (Node.js)
 *
 * The coordinator decomposes complex tasks and delegates to specialized
 * subagents with isolated contexts.
 *
 * YOUR TASK: Fill in the TODO sections to implement the coordinator pattern.
 *
 * Usage:
 *     node subagent_coordinator.js
 */

// --- Mock data ---

const MOCK_FILING_DATA = {
  "UCC-2024-NY-0012847": {
    filing_number: "UCC-2024-NY-0012847",
    status: "Active",
    state: "NY",
    debtor: "Greenfield Logistics LLC",
    secured_party: "Atlantic Capital Partners",
    filing_date: "2024-03-15",
    collateral: "All accounts receivable, inventory, equipment",
  },
  "UCC-2023-CA-0098312": {
    filing_number: "UCC-2023-CA-0098312",
    status: "Active",
    state: "CA",
    debtor: "Greenfield Logistics West LLC",
    secured_party: "Pacific Trust Holdings",
    filing_date: "2023-09-01",
    collateral: "Inventory and warehouse equipment",
  },
};

const MOCK_ENTITY_DATA = {
  "Greenfield Logistics LLC": {
    canonical_name: "Greenfield Logistics LLC",
    aliases: ["Greenfield Logistics", "Greenfield Log. LLC", "GL LLC"],
    state_of_formation: "NY",
    related_entities: ["Greenfield Logistics West LLC", "Greenfield Transport Inc"],
    ucc_filings: ["UCC-2024-NY-0012847"],
    confidence: 0.95,
  },
  "Greenfield Logistics West LLC": {
    canonical_name: "Greenfield Logistics West LLC",
    aliases: ["GL West", "Greenfield West"],
    state_of_formation: "CA",
    related_entities: ["Greenfield Logistics LLC"],
    ucc_filings: ["UCC-2023-CA-0098312"],
    confidence: 0.92,
  },
};

const MOCK_RISK_DATA = {
  "Greenfield Logistics LLC": {
    risk_score: 0.35,
    risk_level: "LOW",
    factors: ["No prior defaults", "Active 5+ years", "Single active lien"],
    total_lien_value: 250000,
    last_updated: "2024-12-01",
  },
  "Greenfield Logistics West LLC": {
    risk_score: 0.42,
    risk_level: "LOW",
    factors: ["No prior defaults", "Active 2+ years", "Single active lien"],
    total_lien_value: 120000,
    last_updated: "2024-11-15",
  },
};

// --- SubAgent ---

class SubAgent {
  constructor(name, role, systemPrompt, tools = []) {
    this.name = name;
    this.role = role;
    this.systemPrompt = systemPrompt;
    this.tools = tools;
    this.messages = [];
    this.result = null;
    this.executionTimeMs = 0;
  }

  execute(taskDescription, context = null) {
    const startTime = Date.now();

    console.log(`\n    [${this.name}] Starting: ${taskDescription.slice(0, 60)}...`);
    if (context) {
      console.log(`    [${this.name}] Received context: ${JSON.stringify(context).slice(0, 80)}...`);
    }

    this.messages.push({ role: "user", content: taskDescription, context });

    this.result = this._simulateWork(taskDescription, context);

    this.executionTimeMs = Date.now() - startTime;

    console.log(`    [${this.name}] Complete (${this.executionTimeMs}ms)`);
    console.log(`    [${this.name}] Result keys: ${Object.keys(this.result).join(", ")}`);

    return this.result;
  }

  _simulateWork(task, context) {
    switch (this.role) {
      case "filing_search":
        return this._filingSearch(context);
      case "entity_resolution":
        return this._entityResolution(context);
      case "risk_scoring":
        return this._riskScoring(context);
      default:
        return { error: `Unknown role: ${this.role}` };
    }
  }

  _filingSearch(context) {
    const entityName = context?.entity_name || "";
    const results = [];

    for (const filing of Object.values(MOCK_FILING_DATA)) {
      if (filing.debtor.toLowerCase().includes(entityName.toLowerCase())) {
        results.push(filing);
      }
    }

    const entityInfo = MOCK_ENTITY_DATA[entityName] || {};
    for (const related of entityInfo.related_entities || []) {
      for (const filing of Object.values(MOCK_FILING_DATA)) {
        if (
          filing.debtor.toLowerCase().includes(related.toLowerCase()) &&
          !results.includes(filing)
        ) {
          results.push(filing);
        }
      }
    }

    return {
      filings_found: results.length,
      filings: results,
      search_entity: entityName,
      states_covered: [...new Set(results.map((f) => f.state))],
    };
  }

  _entityResolution(context) {
    const entityName = context?.entity_name || "";
    const entity = MOCK_ENTITY_DATA[entityName] || {};
    const relatedEntities = (entity.related_entities || [])
      .map((name) => MOCK_ENTITY_DATA[name])
      .filter(Boolean);

    return {
      canonical_entity: entity,
      related_entities: relatedEntities,
      total_entities: 1 + relatedEntities.length,
      resolution_confidence: entity.confidence || 0,
    };
  }

  _riskScoring(context) {
    const entities = context?.entities || [];
    const riskProfiles = entities
      .map((name) => {
        const risk = MOCK_RISK_DATA[name];
        return risk ? { entity: name, ...risk } : null;
      })
      .filter(Boolean);

    const avgScore =
      riskProfiles.length > 0
        ? riskProfiles.reduce((s, r) => s + r.risk_score, 0) / riskProfiles.length
        : 0;
    const totalLien = riskProfiles.reduce((s, r) => s + r.total_lien_value, 0);

    return {
      individual_profiles: riskProfiles,
      aggregate_risk_score: Math.round(avgScore * 1000) / 1000,
      aggregate_risk_level: avgScore < 0.4 ? "LOW" : avgScore < 0.7 ? "MEDIUM" : "HIGH",
      total_lien_exposure: totalLien,
    };
  }
}

// --- Coordinator ---

class Coordinator {
  constructor() {
    this.subagents = {};
    this.executionLog = [];
  }

  registerSubagent(subagent) {
    this.subagents[subagent.role] = subagent;
    console.log(`  [Coordinator] Registered subagent: ${subagent.name} (role: ${subagent.role})`);
  }

  processRequest(request) {
    console.log(`\n${"=".repeat(60)}`);
    console.log("Coordinator: Processing request");
    console.log("=".repeat(60));
    console.log(`  Request: ${request.slice(0, 80)}...`);

    const subtasks = this.decomposeTask(request);
    console.log(`\n  Decomposed into ${subtasks.length} subtasks:`);
    for (const st of subtasks) {
      console.log(`    - [${st.role}] ${st.description.slice(0, 60)}...`);
    }

    // TODO: Execute subtasks
    //
    // Create an empty results object: const results = {};
    // For each subtask:
    //   1. Get the role from subtask
    //   2. Get the subagent: this.subagents[role]
    //   3. If no subagent, console.log a warning and continue
    //   4. Call subagent.execute(subtask.description, subtask.context || {})
    //   5. Store: results[role] = result
    //   6. Push to this.executionLog: {timestamp, subagent name, role, task, execution_time_ms}
    //
    //   IMPORTANT: After entity_resolution completes, enrich risk_scoring:
    //   - const entities = [result.canonical_entity?.canonical_name || ""]
    //   - Add names from result.related_entities
    //   - Find the risk_scoring subtask and update its context.entities

    const results = {}; // <-- Your implementation goes after this line

    return this.aggregateResults(results);
  }

  decomposeTask(request) {
    const entityName = "Greenfield Logistics LLC";
    return [
      {
        role: "filing_search",
        description: `Search for all UCC filings related to ${entityName} across all states`,
        context: { entity_name: entityName },
      },
      {
        role: "entity_resolution",
        description: `Resolve ${entityName} to canonical form and find all related entities`,
        context: { entity_name: entityName },
      },
      {
        role: "risk_scoring",
        description: `Calculate risk scores for ${entityName} and all related entities`,
        context: { entities: [entityName] },
      },
    ];
  }

  aggregateResults(results) {
    console.log(`\n  [Coordinator] Aggregating results from ${Object.keys(results).length} subagents...`);

    const filing = results.filing_search || {};
    const entity = results.entity_resolution || {};
    const risk = results.risk_scoring || {};

    // TODO: Build the aggregated report
    //
    // Return an object with three keys: summary, findings, provenance
    //
    // summary: { request_type, timestamp, subagents_used }
    // findings: { total_filings, states_covered, total_related_entities, resolution_confidence,
    //             aggregate_risk_level, aggregate_risk_score, total_lien_exposure }
    // provenance: { filing_data: {source, filings}, entity_data: {source, canonical, related},
    //               risk_data: {source, profiles} }

    // Replace the line below with your implementation
    return { summary: {}, findings: {}, provenance: {} };
  }
}

// --- Main ---

function main() {
  console.log("=".repeat(60));
  console.log("M26 Lab — Coordinator + Subagent Pattern");
  console.log("=".repeat(60));

  const coordinator = new Coordinator();

  console.log("\n--- Registering subagents ---");
  coordinator.registerSubagent(
    new SubAgent("FilingSearchAgent", "filing_search", "Search UCC filing databases.", [
      "search_filings",
      "search_by_debtor",
    ])
  );
  coordinator.registerSubagent(
    new SubAgent("EntityResolutionAgent", "entity_resolution", "Resolve entity names.", [
      "resolve_entity",
      "find_aliases",
    ])
  );
  coordinator.registerSubagent(
    new SubAgent("RiskScoringAgent", "risk_scoring", "Calculate risk scores.", [
      "calculate_risk",
      "get_lien_history",
    ])
  );

  console.log("\n--- Processing request ---");
  const report = coordinator.processRequest(
    "Research Greenfield Logistics LLC across all states. Find all filings, resolve related entities, and calculate aggregate risk exposure."
  );

  console.log(`\n${"=".repeat(60)}`);
  console.log("Final Aggregated Report");
  console.log("=".repeat(60));

  const { summary = {}, findings = {} } = report;
  console.log(`\n  Request type: ${summary.request_type || "N/A"}`);
  console.log(`  Subagents used: ${(summary.subagents_used || []).join(", ") || "N/A"}`);
  console.log(`\n  Findings:`);
  console.log(`    Total filings found: ${findings.total_filings ?? "N/A"}`);
  console.log(`    States covered: ${(findings.states_covered || []).join(", ") || "N/A"}`);
  console.log(`    Related entities: ${findings.total_related_entities ?? "N/A"}`);
  const conf = findings.resolution_confidence;
  console.log(`    Entity resolution confidence: ${typeof conf === "number" ? (conf * 100).toFixed(0) + "%" : "N/A"}`);
  console.log(`    Aggregate risk level: ${findings.aggregate_risk_level || "N/A"}`);
  console.log(`    Aggregate risk score: ${findings.aggregate_risk_score ?? "N/A"}`);
  const lien = findings.total_lien_exposure;
  console.log(`    Total lien exposure: ${typeof lien === "number" ? "$" + lien.toLocaleString() : "N/A"}`);

  console.log(`\n  Provenance:`);
  for (const [name, data] of Object.entries(report.provenance || {})) {
    console.log(`    ${name}: from ${data.source || "N/A"}`);
  }

  console.log(`\n${"=".repeat(60)}`);
  console.log("Execution Log");
  console.log("=".repeat(60));
  for (const entry of coordinator.executionLog) {
    console.log(`  [${entry.subagent}] ${entry.task} (${entry.execution_time_ms}ms)`);
  }

  console.log(`\n${"=".repeat(60)}`);
  console.log("Key Takeaways");
  console.log("=".repeat(60));
  console.log(`
    1. Decompose complex tasks into specialized subtasks
    2. Each subagent has isolated context (security + efficiency)
    3. Coordinator explicitly controls what context each subagent receives
    4. Results are aggregated with provenance tracking
    5. Downstream subtasks can receive enriched context from earlier results
  `);

  console.log("[OK] Lab Step 4 complete — Coordinator + subagent pattern\n");
}

main();
