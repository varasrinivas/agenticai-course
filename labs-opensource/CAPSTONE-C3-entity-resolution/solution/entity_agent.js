/**
 * CAPSTONE C3: ReAct Entity Resolution Agent — SOLUTION (Node.js)
 * ================================================================
 * Run: node entity_agent.js
 */

import OpenAI from "openai";
import { fuzzyMatchScore, getBusinessRegistryData, getFilingDetails,
         mergeEntityProfile, searchFilingsByName } from "./entity_tools.js";

const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });
const MODEL = "mistral";

const SYSTEM_PROMPT = `You are an Entity Resolution Agent for a commercial data provider.
Given a business entity name, you determine whether UCC filing records
under different name variations refer to the same real-world company.

## Your Reasoning Process (ReAct)
For each resolution request, think step by step:
1. THINK: What do I know? What do I need to find out?
2. ACT: Call the appropriate tool to gather evidence.
3. OBSERVE: What did the tool return? What does it tell me?
4. REPEAT until you have enough evidence to make a decision.

## Decision Criteria
- token_sort_ratio >= 0.90 AND same state AND same address -> MERGE (high confidence)
- token_sort_ratio >= 0.80 AND same state -> LIKELY MERGE (verify with registry)
- token_sort_ratio >= 0.70 AND different state -> INVESTIGATE (check registry)
- token_sort_ratio < 0.70 -> DISTINCT ENTITY

## Output Format
After resolution, call merge_entity_profile with your findings.
Include a confidence score (0.0-1.0) based on evidence strength.
Explain your reasoning for each merge/separate decision.

## Rules
- Always check the business registry for ambiguous matches.
- If registry data is unavailable, lower your confidence accordingly.
- Never force a merge — flag conflicts for human review.
- If there are 10+ candidates, filter by state before matching.`;

const TOOLS = [
  { type: "function", function: {
    name: "search_filings_by_name",
    description: "Search UCC filings by business name across states. Returns candidate entities with filing counts.",
    parameters: { type: "object", properties: {
      business_name: { type: "string" }, state: { type: "string" },
      match_type: { type: "string", enum: ["exact", "fuzzy"] } },
      required: ["business_name"] } } },
  { type: "function", function: {
    name: "fuzzy_match_score",
    description: "Compute similarity scores between two entity names using normalization and token sort ratio.",
    parameters: { type: "object", properties: {
      entity_a: { type: "string" }, entity_b: { type: "string" } },
      required: ["entity_a", "entity_b"] } } },
  { type: "function", function: {
    name: "get_filing_details",
    description: "Get full filing details (secured parties, collateral, amounts) for an entity in a state.",
    parameters: { type: "object", properties: {
      business_name: { type: "string" }, state: { type: "string" } },
      required: ["business_name", "state"] } } },
  { type: "function", function: {
    name: "get_business_registry_data",
    description: "Cross-reference entity against official SOS business registry for address and status.",
    parameters: { type: "object", properties: {
      business_name: { type: "string" }, state: { type: "string" } },
      required: ["business_name", "state"] } } },
  { type: "function", function: {
    name: "merge_entity_profile",
    description: "Create a merged entity profile from confirmed matches with a confidence score.",
    parameters: { type: "object", properties: {
      primary_entity: { type: "object" }, merge_candidates: { type: "array" },
      confidence: { type: "number" } },
      required: ["primary_entity", "merge_candidates", "confidence"] } } },
];

const HANDLERS = {
  search_filings_by_name: (a) => searchFilingsByName(a.business_name, a.state, a.match_type),
  fuzzy_match_score: (a) => fuzzyMatchScore(a.entity_a, a.entity_b),
  get_filing_details: (a) => getFilingDetails(a.business_name, a.state),
  get_business_registry_data: (a) => getBusinessRegistryData(a.business_name, a.state),
  merge_entity_profile: (a) => mergeEntityProfile(a.primary_entity, a.merge_candidates, a.confidence),
};

async function runEntityAgent(query, verbose = true) {
  const messages = [
    { role: "system", content: SYSTEM_PROMPT },
    { role: "user", content: query },
  ];

  for (let i = 0; i < 15; i++) { // resolution legitimately needs 8-12 tool calls
    let response;
    try {
      response = await client.chat.completions.create({
        model: MODEL,
        messages,
        tools: TOOLS,
      });
    } catch (e) {
      return `Error calling model: ${e.message}`;
    }

    const choice = response.choices[0];

    if (choice.finish_reason === "tool_calls") {
      const toolCalls = choice.message.tool_calls ?? [];

      // Push the assistant message with tool_calls re-serialized
      messages.push({
        role: "assistant",
        content: choice.message.content,
        tool_calls: toolCalls.map((tc) => ({
          id: tc.id, type: "function",
          function: { name: tc.function.name, arguments: tc.function.arguments },
        })),
      });

      for (const tc of toolCalls) {
        if (verbose) console.log(`  [tool] ${tc.function.name}(${tc.function.arguments.slice(0, 80)})`);
        const handler = HANDLERS[tc.function.name];
        let args;
        try {
          args = JSON.parse(tc.function.arguments);
        } catch {
          args = {}; // malformed args != crash
        }
        const result = handler ? handler(args)
          : { is_error: true, error_category: "UNKNOWN_TOOL" };
        messages.push({ role: "tool", tool_call_id: tc.id, content: JSON.stringify(result) });
      }
    } else if (choice.finish_reason === "stop") {
      return choice.message.content ?? "Resolution complete (no text output).";
    }
  }

  return "Resolution exceeded maximum iterations (15).";
}

const result = await runEntityAgent(
  "Resolve entity: Acme Logistics LLC in Delaware. " +
  "Check for name variations across states and produce a merged profile."
);
console.log("\n" + "=".repeat(60));
console.log("RESOLUTION:");
console.log("=".repeat(60));
console.log(result);
