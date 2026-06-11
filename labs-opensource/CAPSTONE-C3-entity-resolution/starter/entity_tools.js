/**
 * CAPSTONE C3: Mock Entity Resolution Tools (COMPLETE — Node.js)
 * ===============================================================
 * Same logic as entity_tools.py. Tools never throw — structured errors.
 */

const SUFFIX_RE = /\b(llc|l l c|inc|incorporated|corp|corporation|company|co|ltd)\b/gi;

function normalize(name) {
  return name.toLowerCase().trim().replace(/[,.\-]/g, " ").replace(/\s+/g, " ")
    .replace(SUFFIX_RE, "").replace(/\s+/g, " ").trim();
}

const MOCK_CANDIDATES = {
  "acme logistics llc": [
    { name: "ACME LOGISTICS, L.L.C.", state: "DE", filing_count: 3, most_recent: "2024-01-15" },
    { name: "Acme Logistics Company", state: "DE", filing_count: 1, most_recent: "2023-08-20" },
    { name: "Acme Logistics Inc.", state: "NY", filing_count: 2, most_recent: "2023-12-01" },
  ],
  "buildright construction": [
    { name: "BuildRight Construction LLC", state: "NY", filing_count: 1, most_recent: "2024-01-10" },
    { name: "Build Right Construction", state: "NY", filing_count: 1, most_recent: "2022-03-15" },
  ],
};

export function searchFilingsByName(businessName, state = null) {
  try {
    const key = businessName.toLowerCase().trim();
    let candidates = MOCK_CANDIDATES[key] || [];
    if (state) candidates = candidates.filter((c) => c.state === state.toUpperCase());
    if (!candidates.length) {
      return { is_error: true, error_category: "NO_RESULTS", is_retryable: false,
               context: `No filings found for '${businessName}'` };
    }
    return { is_error: false, candidates, total: candidates.length };
  } catch (e) {
    return { is_error: true, error_category: "INTERNAL_ERROR", is_retryable: true, context: e.message };
  }
}

export function fuzzyMatchScore(entityA, entityB) {
  try {
    if (!entityA || !entityB) {
      return { is_error: true, error_category: "EMPTY_INPUT", is_retryable: false };
    }
    const normA = normalize(entityA), normB = normalize(entityB);
    const exact = entityA.toLowerCase() === entityB.toLowerCase() ? 1.0 : 0.7;
    const tokA = new Set(normA.split(" ")), tokB = new Set(normB.split(" "));
    const inter = [...tokA].filter((t) => tokB.has(t)).length;
    const normalized = normA === normB ? 1.0
      : parseFloat((inter / Math.max(new Set([...tokA, ...tokB]).size, 1)).toFixed(2));
    const tokenSort = Math.min(normalized > 0.8 ? parseFloat((normalized * 1.03).toFixed(2)) : normalized, 1.0);
    const avg = parseFloat(((exact + normalized + tokenSort) / 3).toFixed(2));
    const rec = avg >= 0.85 ? "likely_match" : avg >= 0.65 ? "possible_match" : "unlikely_match";
    return { is_error: false, entity_a: entityA, entity_b: entityB,
             scores: { exact, normalized, token_sort_ratio: tokenSort }, recommendation: rec };
  } catch (e) {
    return { is_error: true, error_category: "INTERNAL_ERROR", is_retryable: true, context: e.message };
  }
}

const MOCK_FILINGS = {
  "acme logistics, l.l.c.|DE": { filings: [
    { filing_number: "2023-1234567", secured_party: "First National Bank",
      collateral: "All inventory and equipment", status: "active", estimated_amount: 750000 },
    { filing_number: "2022-9876543", secured_party: "Delaware Capital Partners",
      collateral: "All vehicles", status: "active", estimated_amount: 350000 },
    { filing_number: "2024-0011223", secured_party: "First National Bank",
      collateral: "Accounts receivable", status: "active", estimated_amount: 1200000 },
  ]},
};

export function getFilingDetails(businessName, state) {
  try {
    const key = `${businessName.toLowerCase().trim()}|${state.toUpperCase()}`;
    const result = MOCK_FILINGS[key];
    return result ? { is_error: false, ...result } : { is_error: false, filings: [] };
  } catch (e) {
    return { is_error: true, error_category: "INTERNAL_ERROR", is_retryable: true, context: e.message };
  }
}

const MOCK_REGISTRY = {
  "acme logistics llc|DE": {
    entity_name: "Acme Logistics LLC", state: "DE", entity_type: "LLC",
    file_number: "DE-LLC-2019-4567890", formation_date: "2019-03-15",
    status: "active", principal_address: "456 Commerce Blvd, Dover, DE 19901",
  },
  "acme logistics inc.|NY": {
    entity_name: "Acme Logistics Inc.", state: "NY", entity_type: "Corporation",
    file_number: "NY-CORP-2020-1234567", formation_date: "2020-07-01",
    status: "active", principal_address: "100 Broadway, New York, NY 10001",
  },
};

export function getBusinessRegistryData(businessName, state) {
  try {
    const key = `${businessName.toLowerCase().trim()}|${state.toUpperCase()}`;
    const result = MOCK_REGISTRY[key];
    if (result) return { is_error: false, ...result };
    // NOT_FOUND is a SIGNAL (lower confidence), not a crash
    return { is_error: true, error_category: "NOT_FOUND", is_retryable: false,
             context: `No registry entry for '${businessName}' in ${state}` };
  } catch (e) {
    return { is_error: true, error_category: "INTERNAL_ERROR", is_retryable: true, context: e.message };
  }
}

export function mergeEntityProfile(primaryEntity, mergeCandidates, confidence) {
  try {
    if (confidence < 0.5) {
      return { is_error: true, error_category: "INSUFFICIENT_EVIDENCE", is_retryable: false,
               context: `Confidence ${confidence} below 0.5 threshold` };
    }
    const totalFilings = mergeCandidates.reduce((s, c) => s + (c.filing_count || 0), 0)
      + (primaryEntity.filing_count || 0);
    const totalLien = mergeCandidates.reduce((s, c) => s + (c.estimated_amount || 0), 0)
      + (primaryEntity.estimated_amount || 0);
    const states = [...new Set([primaryEntity.state || "", ...mergeCandidates.map((c) => c.state || "")])];
    return { is_error: false,
      merged_profile_id: `MP-${(primaryEntity.name || "unknown").slice(0, 10)}-${Math.round(confidence * 100)}pct`,
      canonical_name: primaryEntity.name || "Unknown",
      total_filings: totalFilings, total_lien_exposure: totalLien,
      states, confidence,
      merge_log: mergeCandidates.map((c) => `Merged '${c.name || ""}' (score: ${c.match_score || "N/A"})`) };
  } catch (e) {
    return { is_error: true, error_category: "INTERNAL_ERROR", is_retryable: true, context: e.message };
  }
}
