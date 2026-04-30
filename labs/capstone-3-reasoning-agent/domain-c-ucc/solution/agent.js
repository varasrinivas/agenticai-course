/**
 * UCC Entity Resolution Agent — ReAct Agent (Node.js Solution)
 *
 * Complete implementation using the Anthropic Node.js SDK.
 */

import Anthropic from "@anthropic-ai/sdk";

const MODEL = "claude-sonnet-4-6";
const MAX_ITERATIONS = 15;

const SYSTEM_PROMPT = `You are a UCC Entity Resolution Agent. Your job is to take a business name and
resolve it across UCC filings in multiple states, identifying all name variations,
confirming entity identity, and building a unified entity profile.

You MUST follow this reasoning process:
1. FIRST, search for filings by the given business name across all states
2. THEN, examine the results for name variations
3. NEXT, use fuzzy matching to score how closely name variations match
4. THEN, look up the business registry data to confirm identity (using EIN)
5. CHECK for entities with similar names but DIFFERENT EINs
6. FINALLY, merge all confirmed filings into a unified entity profile

Use the EIN as the definitive identifier. Same EIN = same entity. Different EIN = different entity.`;

// ---------------------------------------------------------------------------
// Tool Schemas
// ---------------------------------------------------------------------------
const TOOL_SCHEMAS = [
  {
    name: "search_filings_by_name",
    description: "Search UCC filings across all states for a given business name. Use this FIRST.",
    input_schema: {
      type: "object",
      properties: {
        business_name: { type: "string", description: "The business name to search for" },
        state: { type: "string", description: "Optional: limit search to a specific state" },
      },
      required: ["business_name"],
    },
  },
  {
    name: "fuzzy_match_score",
    description: "Calculate a fuzzy match confidence score between two business names (0.0-1.0).",
    input_schema: {
      type: "object",
      properties: {
        name_a: { type: "string", description: "First business name" },
        name_b: { type: "string", description: "Second business name" },
      },
      required: ["name_a", "name_b"],
    },
  },
  {
    name: "get_filing_details",
    description: "Get full details of a specific UCC filing by filing number.",
    input_schema: {
      type: "object",
      properties: {
        filing_number: { type: "string", description: "The UCC filing number" },
        state: { type: "string", description: "The state of the filing" },
      },
      required: ["filing_number", "state"],
    },
  },
  {
    name: "get_business_registry_data",
    description: "Look up official business registration data by EIN or business name.",
    input_schema: {
      type: "object",
      properties: {
        ein: { type: "string", description: "The business EIN/Tax ID" },
        business_name: { type: "string", description: "The business name" },
      },
      required: [],
    },
  },
  {
    name: "merge_entity_profile",
    description: "Merge filings into a unified entity profile. Use as FINAL step.",
    input_schema: {
      type: "object",
      properties: {
        entity_name: { type: "string" },
        ein: { type: "string" },
        name_variations: { type: "array", items: { type: "string" } },
        filing_numbers: { type: "array", items: { type: "string" } },
        states_with_filings: { type: "array", items: { type: "string" } },
        total_secured_parties: { type: "integer" },
        risk_notes: { type: "string" },
      },
      required: ["entity_name", "ein", "name_variations", "filing_numbers", "states_with_filings", "total_secured_parties", "risk_notes"],
    },
  },
];

// ---------------------------------------------------------------------------
// Mock Data (condensed for JS)
// ---------------------------------------------------------------------------
const UCC_FILINGS = {
  CA: {
    "CA-2023-0847291": { filing_number: "CA-2023-0847291", state: "CA", debtor_name: "Acme Corp", debtor_ein: "94-3829471", secured_party: "Pacific Commerce Bank", filing_date: "2023-03-15", status: "active", collateral_description: "All inventory, equipment, accounts receivable, and general intangibles" },
    "CA-2024-0112834": { filing_number: "CA-2024-0112834", state: "CA", debtor_name: "ACME CORPORATION", debtor_ein: "94-3829471", secured_party: "Western Capital Lending LLC", filing_date: "2024-01-22", status: "active", collateral_description: "Equipment and fixtures" },
    "CA-2021-0289451": { filing_number: "CA-2021-0289451", state: "CA", debtor_name: "Acme Corp dba AcmeTech Solutions", debtor_ein: "94-3829471", secured_party: "Silicon Valley Equipment Finance", filing_date: "2021-05-20", status: "active", collateral_description: "Specific equipment: CNC machinery" },
    "CA-2023-0991204": { filing_number: "CA-2023-0991204", state: "CA", debtor_name: "Acme Holdings LLC", debtor_ein: "94-5501287", secured_party: "Bay Area Commercial Lending", filing_date: "2023-11-05", status: "active", collateral_description: "Membership interests and equity in subsidiaries" },
  },
  NV: {
    "NV-2023-0034521": { filing_number: "NV-2023-0034521", state: "NV", debtor_name: "Acme Corporation", debtor_ein: "94-3829471", secured_party: "Nevada Business Finance Corp", filing_date: "2023-06-12", status: "active", collateral_description: "Inventory and equipment at Reno facility" },
  },
  TX: {
    "TX-2022-1847592": { filing_number: "TX-2022-1847592", state: "TX", debtor_name: "Acme Corp", debtor_ein: "94-3829471", secured_party: "Lone Star Business Credit", filing_date: "2022-11-03", status: "active", collateral_description: "All inventory, accounts receivable, and equipment" },
    "TX-2024-0229183": { filing_number: "TX-2024-0229183", state: "TX", debtor_name: "ACME CORP", debtor_ein: "94-3829471", secured_party: "Texas Regional Bank", filing_date: "2024-03-10", status: "active", collateral_description: "Line of credit secured by accounts receivable" },
  },
  NY: {
    "NY-2023-0558291": { filing_number: "NY-2023-0558291", state: "NY", debtor_name: "Acme Corporation", debtor_ein: "94-3829471", secured_party: "Manhattan Commercial Finance", filing_date: "2023-07-18", status: "active", collateral_description: "Accounts receivable, contract rights" },
  },
  DE: {
    "DE-2021-0091447": { filing_number: "DE-2021-0091447", state: "DE", debtor_name: "Acme Corp", debtor_ein: "94-3829471", secured_party: "Delaware Trust Financial", filing_date: "2021-09-30", status: "active", collateral_description: "All assets now owned or hereafter acquired" },
  },
};

const BUSINESS_REGISTRY = {
  "94-3829471": {
    ein: "94-3829471", legal_name: "Acme Corporation",
    dba_names: ["Acme Corp", "AcmeTech Solutions", "Acme Industrial"],
    entity_type: "Corporation", state_of_incorporation: "DE",
    name_history: [
      { name: "Acme Corp", effective_date: "2005-03-22", end_date: "2022-01-15" },
      { name: "Acme Corporation", effective_date: "2022-01-15", end_date: null },
    ],
    addresses: {
      headquarters: "1200 Industrial Blvd, Suite 400, San Jose, CA 95112",
      branches: ["Reno, NV", "Austin, TX", "New York, NY"],
    },
  },
  "94-5501287": {
    ein: "94-5501287", legal_name: "Acme Holdings LLC",
    dba_names: [], entity_type: "LLC",
    notes: "Parent holding company of Acme Corporation (EIN 94-3829471).",
  },
};

// ---------------------------------------------------------------------------
// Tool Handlers
// ---------------------------------------------------------------------------
function normalize(name) { return name.toUpperCase().trim().replace(/\s+/g, " "); }
function tokenize(name) {
  const noise = new Set(["DBA", "D/B/A", "THE", "A", "AN", "AND", "&", "OF", "FORMERLY"]);
  return new Set(normalize(name).split(" ").filter((t) => !noise.has(t)));
}

function searchFilingsByName({ business_name, state }) {
  const search = normalize(business_name);
  const results = [];
  const statesToSearch = state ? [state] : Object.keys(UCC_FILINGS);

  for (const st of statesToSearch) {
    for (const [fn, filing] of Object.entries(UCC_FILINGS[st] || {})) {
      const debtor = normalize(filing.debtor_name);
      if (debtor.includes(search) || search.includes(debtor)) {
        results.push({ state: st, filing_number: fn, debtor_name: filing.debtor_name, debtor_ein: filing.debtor_ein, secured_party: filing.secured_party, filing_date: filing.filing_date, status: filing.status });
      } else {
        const searchTokens = tokenize(business_name);
        const debtorTokens = tokenize(filing.debtor_name);
        const overlap = [...searchTokens].filter((t) => debtorTokens.has(t));
        if (overlap.length >= 1 && overlap.length / searchTokens.size >= 0.5) {
          results.push({ state: st, filing_number: fn, debtor_name: filing.debtor_name, debtor_ein: filing.debtor_ein, secured_party: filing.secured_party, filing_date: filing.filing_date, status: filing.status, match_type: "partial" });
        }
      }
    }
  }
  return { query: business_name, results_count: results.length, results };
}

function fuzzyMatchScore({ name_a, name_b }) {
  const a = normalize(name_a), b = normalize(name_b);
  if (a === b) return { name_a, name_b, score: 1.0, match_type: "exact", details: "Identical after normalization." };
  if (a.includes(b) || b.includes(a)) return { name_a, name_b, score: 0.85, match_type: "substring", details: "One name is substring of other." };

  const tA = tokenize(name_a), tB = tokenize(name_b);
  const shared = [...tA].filter((t) => tB.has(t));
  const total = new Set([...tA, ...tB]);
  const score = Math.round((shared.length / total.size) * 100) / 100;

  return { name_a, name_b, score, match_type: score >= 0.6 ? "token_overlap" : "low_match", details: `${shared.length}/${total.size} tokens shared.` };
}

function getFilingDetails({ filing_number, state }) {
  const filings = UCC_FILINGS[state];
  if (!filings) return { error: `No filings for state ${state}` };
  return filings[filing_number] || { error: `Filing ${filing_number} not found in ${state}` };
}

function getBusinessRegistryData({ ein, business_name }) {
  if (ein) return BUSINESS_REGISTRY[ein] || { error: `No business with EIN ${ein}` };
  if (business_name) {
    const search = normalize(business_name);
    for (const entry of Object.values(BUSINESS_REGISTRY)) {
      if (normalize(entry.legal_name) === search) return entry;
      if (entry.dba_names?.some((d) => normalize(d) === search)) return entry;
    }
    return { error: `No business matching '${business_name}'` };
  }
  return { error: "Either ein or business_name required" };
}

function mergeEntityProfile({ entity_name, ein, name_variations, filing_numbers, states_with_filings, total_secured_parties, risk_notes }) {
  const dataPoints = filing_numbers.length + name_variations.length + states_with_filings.length;
  const confidence = dataPoints >= 10 ? 0.95 : dataPoints >= 6 ? 0.85 : 0.70;
  return {
    entity_name, ein, name_variations,
    filing_summary: { total_filings: filing_numbers.length, states: states_with_filings, filing_numbers },
    lien_exposure: { total_secured_parties, risk_level: total_secured_parties >= 5 ? "high" : total_secured_parties >= 3 ? "moderate" : "low" },
    risk_assessment: risk_notes, profile_status: "resolved", confidence_score: confidence,
  };
}

const TOOL_HANDLERS = {
  search_filings_by_name: searchFilingsByName,
  fuzzy_match_score: fuzzyMatchScore,
  get_filing_details: getFilingDetails,
  get_business_registry_data: getBusinessRegistryData,
  merge_entity_profile: mergeEntityProfile,
};

function executeTool(name, input) {
  const handler = TOOL_HANDLERS[name];
  if (!handler) return JSON.stringify({ error: `Unknown tool: ${name}` });
  try { return JSON.stringify(handler(input), null, 2); }
  catch (e) { return JSON.stringify({ error: `Tool failed: ${e.message}` }); }
}

// ---------------------------------------------------------------------------
// ReAct Agent Loop
// ---------------------------------------------------------------------------
async function runAgent(userQuery) {
  const client = new Anthropic();
  const messages = [{ role: "user", content: userQuery }];

  console.log("\n" + "=".repeat(70));
  console.log("REASONING TRACE");
  console.log("=".repeat(70));

  for (let step = 1; step <= MAX_ITERATIONS; step++) {
    let response;
    try {
      response = await client.messages.create({ model: MODEL, max_tokens: 4096, system: SYSTEM_PROMPT, tools: TOOL_SCHEMAS, messages });
    } catch (e) {
      console.error(`\n[ERROR] ${e.message}`);
      return `Agent error: ${e.message}`;
    }

    const toolUseBlocks = [];
    const textParts = [];

    for (const block of response.content) {
      if (block.type === "text") {
        textParts.push(block.text);
        console.log(`\n--- Step ${step} ---`);
        console.log(`[THINK] ${block.text}`);
      } else if (block.type === "tool_use") {
        toolUseBlocks.push(block);
        console.log(`\n--- Step ${step} ---`);
        console.log(`[ACT] ${block.name}(${JSON.stringify(block.input)})`);
      }
    }

    if (response.stop_reason === "end_turn") {
      const finalText = textParts.join("\n");
      console.log(`\n[ANSWER] ${finalText.substring(0, 500)}...`);
      return finalText;
    }

    if (response.stop_reason === "tool_use" && toolUseBlocks.length > 0) {
      messages.push({ role: "assistant", content: response.content });
      const toolResults = toolUseBlocks.map((block) => {
        const result = executeTool(block.name, block.input);
        console.log(`[OBSERVE] ${block.name}: ${result.substring(0, 300)}...`);
        return { type: "tool_result", tool_use_id: block.id, content: result };
      });
      messages.push({ role: "user", content: toolResults });
    }
  }
  return "Agent reached maximum iterations.";
}

const query = `Resolve entity: Acme Corp. Find all UCC filings across all states,
identify all name variations, and build a unified entity profile.
Distinguish from any similarly-named but separate businesses.`;

runAgent(query).then((result) => {
  console.log("\n" + "=".repeat(70));
  console.log("FINAL RESULT");
  console.log("=".repeat(70));
  console.log(result);
});
