/**
 * M10 Lab: BM25 + RRF + LLM Re-ranking (Node.js)
 * ===============================================
 * The dense half needs a Chroma server in JS, so this version covers
 * BM25 + RRF (merging BM25 with an LLM-judged list) + LLM re-rank.
 * Run: node hybrid_rag.js
 */

import OpenAI from "openai";

// ── The corpus (COMPLETE) ────────────────────────────────────
const DOCS = [
  "Metformin lowers blood sugar by reducing hepatic glucose production via AMPK activation.",
  "FDA approval number 123-456 was granted for metformin HCl 500mg tablets.",
  "Side effects of metformin include nausea, diarrhea, and abdominal discomfort.",
  "Drug interactions: iodinated contrast agents may cause lactic acidosis; hold metformin 48 hours before procedures.",
  "Metformin is contraindicated in patients with eGFR below 30 mL/min.",
  "FDA approval number 789-012 covers the extended-release formulation.",
  "Kidney function monitoring every 6 months is required for all metformin users.",
];
const DOC_IDS = DOCS.map((_, i) => `doc-${i}`);

// ── Minimal BM25Okapi (COMPLETE — no maintained npm equivalent) ──
class BM25 {
  constructor(docs, k1 = 1.5, b = 0.75) {
    this.k1 = k1;
    this.b = b;
    this.corpus = docs.map((d) => d.toLowerCase().split(/\s+/));
    this.N = this.corpus.length;
    this.avgdl = this.corpus.reduce((s, d) => s + d.length, 0) / this.N;
    this.df = {};
    for (const doc of this.corpus) {
      for (const term of new Set(doc)) this.df[term] = (this.df[term] || 0) + 1;
    }
  }

  idf(term) {
    const df = this.df[term] || 0;
    return Math.log((this.N - df + 0.5) / (df + 0.5) + 1);
  }

  score(docTokens, queryTokens) {
    let score = 0;
    const dl = docTokens.length;
    const tf = {};
    for (const t of docTokens) tf[t] = (tf[t] || 0) + 1;
    for (const qt of queryTokens) {
      const f = tf[qt] || 0;
      score += this.idf(qt) * (f * (this.k1 + 1)) /
        (f + this.k1 * (1 - this.b + (this.b * dl) / this.avgdl));
    }
    return score;
  }

  getScores(query) {
    const qt = query.toLowerCase().split(/\s+/);
    return this.corpus.map((doc) => this.score(doc, qt));
  }
}

// ── Part 1: Reciprocal Rank Fusion (YOUR JOB) ────────────────
/**
 * TODO: for each ranked list, doc at index i earns 1 / (k + i + 1) points;
 * sum across lists into a { docId: score } object and return it.
 * No score normalization — RRF uses RANKS only.
 */
function rrf(rankings, k = 60) {
  // TODO: implement
}

// ── Part 3: LLM Re-ranker (YOUR JOB) ─────────────────────────
const client = new OpenAI({ baseURL: "http://localhost:11434/v1", apiKey: "ollama" });

const JUDGE_SYSTEM =
  "You are a relevance judge. Score how relevant the document is to the " +
  "query on a scale of 0.0 to 1.0. " +
  'Respond with JSON only: {"score": 0.0}';

/**
 * TODO: for each candidate:
 * 1. Call the model with JUDGE_SYSTEM and
 *    `Query: ${query}\n\nDocument: ${c.text.slice(0, 500)}`
 *    (max_tokens: 32, temperature: 0)
 * 2. Parse DEFENSIVELY: strip ```json fences, JSON.parse, .score ?? 0;
 *    on ANY error → 0.0 (never crash on a bad judgment)
 * 3. Attach as c.rerankScore
 * Return candidates sorted by rerankScore descending, topK only.
 * (Promise.all over candidates is fine — Ollama queues the requests.)
 */
async function llmRerank(query, candidates, topK = 5) {
  // TODO: implement
}

// ── Test harness (COMPLETE) ──────────────────────────────────
const bm25 = new BM25(DOCS);
const idToDoc = Object.fromEntries(DOC_IDS.map((id, i) => [id, DOCS[i]]));

function bm25Ranked(query, fetchK = 7) {
  return bm25.getScores(query)
    .map((s, i) => ({ id: DOC_IDS[i], score: s }))
    .sort((a, b) => b.score - a.score)
    .slice(0, fetchK)
    .map((r) => r.id);
}

for (const q of ["FDA approval number 123-456", "what are the side effects"]) {
  console.log(`\nQuery: ${q}`);
  console.log("  BM25 top 3:", bm25Ranked(q, 3));
}

// Hybrid-style demo: merge BM25 ranking with LLM-reranked candidate order
const query = "What are the serious adverse effects of metformin?";
const candidates = bm25Ranked(query, 5).map((id) => ({ id, text: idToDoc[id] }));
const reranked = await llmRerank(query, candidates, 5);
console.log(`\nLLM re-rank for: ${query}`);
for (const r of reranked) console.log(`  [${r.rerankScore.toFixed(2)}] ${r.text.slice(0, 70)}`);

const merged = rrf([bm25Ranked(query, 5), reranked.map((r) => r.id)]);
console.log("\nRRF merge of BM25 + LLM-judged rankings:");
for (const [id, score] of Object.entries(merged).sort(([, a], [, b]) => b - a).slice(0, 3)) {
  console.log(`  [${score.toFixed(4)}] ${idToDoc[id].slice(0, 70)}`);
}
