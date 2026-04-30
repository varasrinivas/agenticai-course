/**
 * M10 Lab - Step 3: Full Advanced RAG Pipeline (Starter)
 * ======================================================
 * Build a complete advanced RAG pipeline with query transformation
 * (HyDE + multi-query), hybrid search, re-ranking, and generation.
 * Compare naive vs advanced RAG on UCC domain questions.
 *
 * KEY CONCEPT: Advanced RAG improves EVERY stage of the pipeline:
 *   1. Query transformation -- rewrite queries for better retrieval
 *   2. Hybrid retrieval -- combine keyword + semantic search
 *   3. Re-ranking -- use Claude to sort by true relevance
 *   4. Generation -- answer with better context = better answers
 *
 * Prerequisites:
 *     npm install @anthropic-ai/sdk dotenv chromadb
 *
 * Usage:
 *     node advanced_rag.js
 */

import Anthropic from "@anthropic-ai/sdk";
import { ChromaClient } from "chromadb";
import "dotenv/config";

const client = new Anthropic();
const MODEL = "claude-sonnet-4-6";

// =============================================================================
// UCC DOCUMENT CORPUS (complete -- do not modify)
// =============================================================================

const UCC_DOCUMENTS = [
  {
    id: "ucc-1",
    title: "UCC-1 Financing Statement Overview",
    content:
      "A UCC-1 financing statement is a legal form that a creditor files to give " +
      "notice that it has an interest in the personal property of a debtor. Filing a " +
      "UCC-1 is the primary method of perfecting a security interest under Article 9 " +
      "of the Uniform Commercial Code. The filing is made with the Secretary of State " +
      "in the state where the debtor is organized. A UCC-1 filing is effective for " +
      "five years from the date of filing and must be renewed by filing a continuation " +
      "statement (UCC-3) before expiration.",
  },
  {
    id: "ucc-2",
    title: "UCC-3 Amendment and Continuation",
    content:
      "A UCC-3 financing statement amendment is used to amend, assign, continue, or " +
      "terminate a UCC-1 filing. A continuation statement must be filed within six " +
      "months before the expiration of the original UCC-1 to keep the filing active. " +
      "If a continuation is not filed, the UCC-1 lapses and the secured party loses " +
      "its perfected status. The UCC-3 form can also be used to amend the collateral " +
      "description, change the debtor or secured party name, or assign the security " +
      "interest to a new party.",
  },
  {
    id: "ucc-3",
    title: "Perfection of Security Interests",
    content:
      "Perfection is the process by which a secured party protects its security " +
      "interest against claims of other creditors. The most common method of " +
      "perfection is filing a UCC-1 financing statement. Other methods include " +
      "taking possession of the collateral or obtaining control over deposit " +
      "accounts, investment property, or letter-of-credit rights. A perfected " +
      "security interest has priority over unperfected interests and over later-filed " +
      "perfected interests. The rules of priority are set forth in Article 9, " +
      "Section 9-322 of the UCC.",
  },
  {
    id: "ucc-4",
    title: "Collateral Types and Descriptions",
    content:
      "Article 9 of the UCC covers security interests in personal property. " +
      "Collateral types include goods (inventory, equipment, farm products, consumer " +
      "goods), accounts receivable, chattel paper, deposit accounts, general " +
      "intangibles (including payment intangibles and software), instruments, " +
      "investment property, and letter-of-credit rights. The financing statement must " +
      "describe the collateral, either by specific listing or by UCC type. A " +
      "super-generic description like 'all assets' is permitted in financing " +
      "statements but not in security agreements.",
  },
  {
    id: "ucc-5",
    title: "Proceeds and After-Acquired Property",
    content:
      "When collateral is sold, exchanged, or otherwise disposed of, the secured " +
      "party's interest automatically attaches to the proceeds. Proceeds include " +
      "whatever is received upon the sale, lease, license, exchange, or other " +
      "disposition of collateral. Cash proceeds and non-cash proceeds are treated " +
      "differently under Article 9. The security interest in proceeds is " +
      "automatically perfected for 20 days; to maintain perfection beyond that, the " +
      "secured party must take additional steps. After-acquired property clauses " +
      "allow a security interest to attach to property the debtor acquires after " +
      "the security agreement is executed.",
  },
  {
    id: "ucc-6",
    title: "Filing Office Rules and Procedures",
    content:
      "UCC filings are made with the appropriate filing office, typically the " +
      "Secretary of State. The filing office must accept or reject a filing within " +
      "prescribed time limits. Common reasons for rejection include failure to " +
      "provide the debtor name, failure to provide the secured party name, or " +
      "failure to pay the filing fee. Electronic filing (e-filing) is available in " +
      "most jurisdictions and is the preferred method. Search logic varies by state, " +
      "but most use a standard search algorithm that ignores case, punctuation, and " +
      "common words (noise words) when matching debtor names.",
  },
  {
    id: "ucc-7",
    title: "Article 9 Section 9-315: Proceeds and Priority",
    content:
      "Section 9-315 of Article 9 governs the disposition of collateral and the " +
      "treatment of proceeds. Under 9-315(a)(1), a security interest continues in " +
      "collateral notwithstanding sale, lease, license, exchange, or other " +
      "disposition unless the secured party authorized the disposition free of the " +
      "security interest. Under 9-315(a)(2), a security interest attaches to any " +
      "identifiable proceeds of collateral. The 20-day automatic perfection rule " +
      "for proceeds is found in 9-315(c) and (d). This section is critical for " +
      "understanding how security interests follow collateral through various " +
      "transactions.",
  },
  {
    id: "ucc-8",
    title: "Debtor Name Requirements",
    content:
      "The debtor name on a UCC-1 financing statement must be exact. For registered " +
      "organizations (corporations, LLCs), the name must match the name on the " +
      "public organic record (e.g., articles of incorporation). For individuals, " +
      "states vary between requiring the name on a driver's license (the 'only if' " +
      "approach) or allowing the individual's legal name. An error in the debtor " +
      "name that makes the filing seriously misleading renders the filing ineffective. " +
      "The standard search logic test is used to determine if an error is seriously " +
      "misleading.",
  },
  {
    id: "ucc-9",
    title: "Priority Rules and Lien Positions",
    content:
      "Priority among competing security interests is generally determined by the " +
      "order of filing or perfection (first-in-time, first-in-right). A perfected " +
      "security interest has priority over an unperfected one. A purchase money " +
      "security interest (PMSI) in goods other than inventory has priority over a " +
      "conflicting security interest if perfected within 20 days of delivery. For " +
      "inventory PMSIs, the secured party must also send notification to holders of " +
      "conflicting security interests. Lien creditors (including bankruptcy trustees) " +
      "take priority over unperfected security interests.",
  },
  {
    id: "ucc-10",
    title: "Termination and Release",
    content:
      "When the debtor has fulfilled all obligations under the security agreement, " +
      "the secured party must file a UCC-3 termination statement within 20 days of " +
      "receiving an authenticated demand from the debtor. For consumer goods, the " +
      "secured party must file a termination within one month of the obligation being " +
      "fulfilled or within 20 days of receiving a demand. Failure to file a " +
      "termination statement can result in liability for the secured party, including " +
      "actual damages and a statutory penalty of $500 per violation. The termination " +
      "extinguishes the effectiveness of the financing statement.",
  },
];

// =============================================================================
// INFRASTRUCTURE (complete -- do not modify)
// =============================================================================

async function setupChromaDB() {
  const chromaClient = new ChromaClient();
  try {
    await chromaClient.deleteCollection({ name: "ucc_documents_advanced" });
  } catch (e) {
    // Ignore
  }
  const collection = await chromaClient.createCollection({
    name: "ucc_documents_advanced",
    metadata: { "hnsw:space": "cosine" },
  });
  await collection.add({
    ids: UCC_DOCUMENTS.map((doc) => doc.id),
    documents: UCC_DOCUMENTS.map((doc) => doc.content),
    metadatas: UCC_DOCUMENTS.map((doc) => ({ title: doc.title })),
  });
  return collection;
}

class BM25Index {
  constructor(documents, k1 = 1.5, b = 0.75) {
    this.k1 = k1;
    this.b = b;
    this.documents = documents;
    this.docCount = documents.length;
    this.docTokens = documents.map(
      (doc) => doc.content.toLowerCase().match(/\w+/g) || []
    );
    this.docLengths = this.docTokens.map((t) => t.length);
    this.avgDocLength =
      this.docLengths.reduce((s, l) => s + l, 0) / this.docCount || 0;
    this.df = {};
    for (const tokens of this.docTokens) {
      for (const term of new Set(tokens)) {
        this.df[term] = (this.df[term] || 0) + 1;
      }
    }
  }

  search(query, topK = 5) {
    const queryTokens = query.toLowerCase().match(/\w+/g) || [];
    const scores = [];
    for (let i = 0; i < this.docCount; i++) {
      let score = 0;
      const dl = this.docLengths[i];
      for (const token of queryTokens) {
        const tf = this.docTokens[i].filter((t) => t === token).length;
        const df = this.df[token] || 0;
        const idf = Math.log((this.docCount - df + 0.5) / (df + 0.5) + 1);
        score +=
          (idf * (tf * (this.k1 + 1))) /
          (tf + this.k1 * (1 - this.b + (this.b * dl) / this.avgDocLength));
      }
      scores.push([i, score]);
    }
    scores.sort((a, b) => b[1] - a[1]);
    return scores.slice(0, topK).map(([i, s]) => ({
      id: this.documents[i].id,
      title: this.documents[i].title,
      content: this.documents[i].content,
      score: s,
    }));
  }
}

async function vectorSearch(query, collection, topK = 5) {
  const results = await collection.query({
    queryTexts: [query],
    nResults: topK,
  });
  return results.ids[0].map((id, i) => ({
    id,
    content: results.documents[0][i],
    title: results.metadatas[0][i].title,
    score: 1 - results.distances[0][i],
  }));
}

function hybridSearchFusion(bm25Results, vectorResults, alpha = 0.5, k = 60) {
  const docInfo = {};
  const bm25Ranks = {};
  const vectorRanks = {};

  bm25Results.forEach((r, i) => {
    bm25Ranks[r.id] = i + 1;
    docInfo[r.id] = { title: r.title, content: r.content };
  });
  vectorResults.forEach((r, i) => {
    vectorRanks[r.id] = i + 1;
    docInfo[r.id] = { title: r.title, content: r.content };
  });

  const allIds = new Set([
    ...Object.keys(bm25Ranks),
    ...Object.keys(vectorRanks),
  ]);
  const fused = [];
  for (const docId of allIds) {
    const br = bm25Ranks[docId] || 1000;
    const vr = vectorRanks[docId] || 1000;
    const rrfScore = alpha * (1 / (k + br)) + (1 - alpha) * (1 / (k + vr));
    const info = docInfo[docId];
    fused.push({
      id: docId,
      title: info.title,
      content: info.content,
      score: rrfScore,
    });
  }
  fused.sort((a, b) => b.score - a.score);
  return fused;
}

async function rerankWithClaude(query, candidates, topK = 3) {
  const scored = [];
  for (const candidate of candidates) {
    try {
      const response = await client.messages.create({
        model: MODEL,
        max_tokens: 200,
        system:
          'Rate the relevance of this passage to the query on a scale of 0-10. ' +
          'Return ONLY a JSON object: {"score": N, "reason": "..."}',
        messages: [
          {
            role: "user",
            content: `Query: ${query}\n\nPassage: ${candidate.content}`,
          },
        ],
      });
      const data = JSON.parse(response.content[0].text.trim());
      scored.push({
        candidate,
        score: data.score || 0,
        reason: data.reason || "",
      });
    } catch (e) {
      scored.push({ candidate, score: 0, reason: "Error scoring" });
    }
  }
  scored.sort((a, b) => b.score - a.score);
  return scored.slice(0, topK).map((s) => s.candidate);
}

// =============================================================================
// NAIVE RAG (complete -- do not modify)
// =============================================================================

async function naiveRag(query, collection) {
  const results = await vectorSearch(query, collection, 3);
  const context = results
    .map((r) => `[${r.title}]\n${r.content}`)
    .join("\n\n");

  const response = await client.messages.create({
    model: MODEL,
    max_tokens: 500,
    system:
      "You are a UCC (Uniform Commercial Code) expert. Answer the question based " +
      "ONLY on the provided context. If the context doesn't contain the answer, say so.",
    messages: [
      { role: "user", content: `Context:\n${context}\n\nQuestion: ${query}` },
    ],
  });

  return {
    answer: response.content[0].text,
    sources: results.map((r) => r.title),
  };
}

// =============================================================================
// OBSERVATION HELPERS (complete -- do not modify)
// =============================================================================

function observe(label, message) {
  console.log(`\n${"=".repeat(60)}`);
  console.log(`[${label}] ${message}`);
  console.log("=".repeat(60));
}

function observeStep(step, message) {
  console.log(`\n  [${step}] ${message}`);
}

// =============================================================================
// YOUR CODE: Query Transformations
// =============================================================================

async function transformQueryHyde(query) {
  /**
   * HyDE (Hypothetical Document Embedding): Ask Claude to write a hypothetical
   * answer to the query. Use that hypothetical answer as the search query.
   *
   * WHY: The hypothetical answer is closer in embedding space to the actual
   * documents than the question is.
   */
  observeStep("HyDE", `Generating hypothetical answer for: ${query}`);

  // ------------------------------------------------------------------
  // TODO 1: Implement HyDE query transformation
  //   Call Claude with:
  //     - system: "Write a short paragraph that would be a perfect answer
  //       to this question about UCC (Uniform Commercial Code) law.
  //       Write as if you are quoting from a legal textbook.
  //       Do NOT say 'based on the context' -- just write the answer directly."
  //     - messages: [{ role: "user", content: query }]
  //     - model: MODEL, max_tokens: 300
  //   Return the text of Claude's response.
  // ------------------------------------------------------------------
  return query; // Fallback: return original query
}

async function transformQueryMulti(query) {
  /**
   * Multi-Query: Generate 3 different search queries from different angles
   * to cast a wider retrieval net.
   *
   * WHY: A single query may miss relevant documents that use different
   * terminology. Multiple queries from different angles catch more.
   */
  observeStep("MULTI-QUERY", `Generating alternative queries for: ${query}`);

  // ------------------------------------------------------------------
  // TODO 2: Implement multi-query transformation
  //   Call Claude with:
  //     - system: "Generate exactly 3 different search queries that would
  //       help answer the user's question about UCC law. Each query should
  //       approach the topic from a different angle or use different
  //       terminology. Return ONLY a JSON array of 3 strings."
  //     - messages: [{ role: "user", content: query }]
  //     - model: MODEL, max_tokens: 300
  //   Parse the JSON array and return it.
  //   Handle errors by returning [query] (the original query).
  // ------------------------------------------------------------------
  return [query]; // Fallback: return original query
}

// =============================================================================
// YOUR CODE: Advanced RAG Pipeline
// =============================================================================

async function advancedRagPipeline(query, collection, bm25Index) {
  /**
   * Full advanced RAG pipeline:
   *   1. Transform the query (HyDE + multi-query)
   *   2. Hybrid search (BM25 + vector) using ALL transformed queries
   *   3. Deduplicate and re-rank with Claude
   *   4. Generate final answer
   */
  observeStep("PIPELINE", "Starting advanced RAG pipeline");

  // ------------------------------------------------------------------
  // TODO 3: Implement the full advanced RAG pipeline
  //
  // Step 1: Query transformation
  //   const hydeQuery = await transformQueryHyde(query);
  //   const multiQueries = await transformQueryMulti(query);
  //   const allQueries = [query, hydeQuery, ...multiQueries];
  //
  // Step 2: Hybrid search with ALL queries
  //   Collect results from hybrid search for each query.
  //   For each q in allQueries:
  //     const bm25Results = bm25Index.search(q, 5);
  //     const vecResults = await vectorSearch(q, collection, 5);
  //     const fused = hybridSearchFusion(bm25Results, vecResults);
  //     Add fused results to a master array
  //
  // Step 3: Deduplicate by doc ID (keep the one with highest score)
  //   Build a Map: docId -> best result
  //   Convert back to a sorted array
  //
  // Step 4: Re-rank top candidates with Claude
  //   const topCandidates = await rerankWithClaude(query, deduped.slice(0, 7), 3);
  //
  // Step 5: Generate final answer
  //   Build context from topCandidates
  //   Call Claude with the same system prompt as naiveRag
  //   Return object with "answer", "sources", "hydeQuery", "multiQueries"
  // ------------------------------------------------------------------
  return {
    answer: "Not implemented yet",
    sources: [],
    hydeQuery: "",
    multiQueries: [],
  };
}

// =============================================================================
// YOUR CODE: Compare Naive vs Advanced
// =============================================================================

async function compareNaiveVsAdvanced(query, collection, bm25Index) {
  /**
   * Run both naive and advanced RAG on the same query and show comparison.
   */
  // ------------------------------------------------------------------
  // TODO 4: Run both pipelines and return comparison
  //   const naiveResult = await naiveRag(query, collection);
  //   const advancedResult = await advancedRagPipeline(query, collection, bm25Index);
  //   return { query, naive: naiveResult, advanced: advancedResult };
  // ------------------------------------------------------------------
  return {
    query,
    naive: { answer: "Not implemented", sources: [] },
    advanced: {
      answer: "Not implemented",
      sources: [],
      hydeQuery: "",
      multiQueries: [],
    },
  };
}

// =============================================================================
// MAIN (complete -- do not modify)
// =============================================================================

console.log("=".repeat(60));
console.log("M10 Lab - Step 3: Full Advanced RAG Pipeline");
console.log("=".repeat(60));

const collection = await setupChromaDB();
const bm25Index = new BM25Index(UCC_DOCUMENTS);

const testQueries = [
  "What happens if I forget to renew my UCC filing?",
  "How do I get first priority on a loan secured by inventory?",
  "Can a security interest follow collateral that gets sold?",
  "What are the requirements for the debtor name on a financing statement?",
  "How do I release a UCC lien after the loan is paid off?",
];

console.log("\n" + "=".repeat(100));
console.log(
  `${"QUERY".padEnd(50)} | ${"NAIVE RAG".padEnd(25)} | ${"ADVANCED RAG".padEnd(25)}`
);
console.log("=".repeat(100));

for (const query of testQueries) {
  observe("COMPARING", query);

  const result = await compareNaiveVsAdvanced(query, collection, bm25Index);

  console.log(`\n  NAIVE RAG:`);
  console.log(`    Sources: ${result.naive.sources.join(", ")}`);
  console.log(`    Answer:  ${result.naive.answer.slice(0, 200)}...`);

  console.log(`\n  ADVANCED RAG:`);
  if (result.advanced.hydeQuery) {
    console.log(
      `    HyDE query: ${result.advanced.hydeQuery.slice(0, 100)}...`
    );
  }
  if (result.advanced.multiQueries) {
    result.advanced.multiQueries.forEach((q, i) => {
      console.log(`    Multi-query ${i + 1}: ${q}`);
    });
  }
  console.log(`    Sources: ${result.advanced.sources.join(", ")}`);
  console.log(`    Answer:  ${result.advanced.answer.slice(0, 200)}...`);

  console.log(`\n  ${"─".repeat(80)}`);
}

console.log("\n" + "=".repeat(60));
console.log("Pipeline comparison complete!");
console.log("=".repeat(60));
