/**
 * M10 Lab - Step 1: Hybrid Search (Starter)
 * ==========================================
 * Build hybrid search combining BM25 keyword search with vector semantic
 * search using reciprocal rank fusion.
 *
 * KEY CONCEPT: Keyword search (BM25) excels at exact term matching.
 * Semantic search (vectors) excels at concept matching. Hybrid search
 * combines both to get the best of both worlds.
 *
 * Prerequisites:
 *     npm install @anthropic-ai/sdk dotenv chromadb
 *
 * Usage:
 *     node hybrid_search.js
 */

import Anthropic from "@anthropic-ai/sdk";
import { ChromaClient } from "chromadb";
import "dotenv/config";

const client = new Anthropic();
const MODEL = "claude-sonnet-4-20250514";

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
// CHROMADB SETUP (complete -- do not modify)
// =============================================================================

async function setupChromaDB() {
  const chromaClient = new ChromaClient();

  // Delete collection if it exists (for reruns)
  try {
    await chromaClient.deleteCollection({ name: "ucc_documents" });
  } catch (e) {
    // Ignore if doesn't exist
  }

  const collection = await chromaClient.createCollection({
    name: "ucc_documents",
    metadata: { "hnsw:space": "cosine" },
  });

  await collection.add({
    ids: UCC_DOCUMENTS.map((doc) => doc.id),
    documents: UCC_DOCUMENTS.map((doc) => doc.content),
    metadatas: UCC_DOCUMENTS.map((doc) => ({ title: doc.title })),
  });

  return collection;
}

// =============================================================================
// VECTOR SEARCH (complete -- do not modify)
// =============================================================================

async function vectorSearch(query, collection, topK = 5) {
  const results = await collection.query({ queryTexts: [query], nResults: topK });

  const searchResults = [];
  for (let i = 0; i < results.ids[0].length; i++) {
    searchResults.push({
      id: results.ids[0][i],
      content: results.documents[0][i],
      title: results.metadatas[0][i].title,
      distance: results.distances[0][i],
      score: 1 - results.distances[0][i],
    });
  }

  return searchResults;
}

// =============================================================================
// OBSERVATION HELPERS (complete -- do not modify)
// =============================================================================

function observe(label, message) {
  console.log(`\n${"=".repeat(60)}`);
  console.log(`[${label}] ${message}`);
  console.log("=".repeat(60));
}

function printResults(label, results, maxDisplay = 5) {
  console.log(`\n--- ${label} ---`);
  for (let i = 0; i < Math.min(results.length, maxDisplay); i++) {
    const r = results[i];
    const score = r.score || 0;
    const title = r.title || "Unknown";
    console.log(`  ${i + 1}. [${score.toFixed(4)}] ${title}`);
    console.log(`     ${r.content.slice(0, 100)}...`);
  }
  console.log();
}

// =============================================================================
// YOUR CODE: BM25 Index
// =============================================================================

class BM25Index {
  /**
   * BM25 (Best Matching 25) is a ranking function used in information retrieval.
   * It scores documents based on term frequency (TF) and inverse document
   * frequency (IDF), with length normalization.
   */
  constructor(documents, k1 = 1.5, b = 0.75) {
    this.k1 = k1;
    this.b = b;
    this.documents = documents;
    this.docCount = documents.length;

    // Tokenize all documents
    this.docTokens = documents.map((doc) => this._tokenize(doc.content));
    this.docLengths = this.docTokens.map((tokens) => tokens.length);
    this.avgDocLength =
      this.docLengths.reduce((sum, len) => sum + len, 0) / this.docCount || 0;

    // ------------------------------------------------------------------
    // TODO 1: Build the document frequency (DF) dictionary
    //   For each document's tokens, count how many documents contain
    //   each unique term. Store in this.df (Map or object: term -> count).
    //   Hint: Use a Set for each document's tokens to avoid counting
    //   a term twice in the same document.
    // ------------------------------------------------------------------
    this.df = {}; // term -> number of documents containing the term
  }

  _tokenize(text) {
    /** Simple tokenizer: lowercase, split on non-alphanumeric characters. */
    return text.toLowerCase().match(/\w+/g) || [];
  }

  _idf(term) {
    /**
     * Compute Inverse Document Frequency for a term.
     * IDF = ln((N - df + 0.5) / (df + 0.5) + 1)
     */
    // ------------------------------------------------------------------
    // TODO 2: Implement IDF calculation
    //   Use this.df to get the document frequency for the term.
    //   If the term is not in this.df, df = 0.
    //   Return: Math.log((this.docCount - df + 0.5) / (df + 0.5) + 1)
    // ------------------------------------------------------------------
    return 0.0;
  }

  _scoreDocument(queryTokens, docIndex) {
    /**
     * Compute BM25 score for a single document given query tokens.
     * Score = sum of IDF(term) * (TF * (k1+1)) / (TF + k1 * (1 - b + b * dl/avgdl))
     */
    // ------------------------------------------------------------------
    // TODO 3: Implement BM25 scoring for a single document
    //   For each query token:
    //     1. Get tf = count of token in this.docTokens[docIndex]
    //     2. Get idf = this._idf(token)
    //     3. Get dl = this.docLengths[docIndex]
    //     4. Compute: idf * (tf * (this.k1 + 1)) / (tf + this.k1 * (1 - this.b + this.b * dl / this.avgDocLength))
    //     5. Sum all terms
    // ------------------------------------------------------------------
    return 0.0;
  }

  search(query, topK = 5) {
    /** Search documents using BM25 scoring. */
    const queryTokens = this._tokenize(query);

    // ------------------------------------------------------------------
    // TODO 4: Score all documents and return topK results
    //   1. For each document, compute _scoreDocument(queryTokens, i)
    //   2. Sort by score descending
    //   3. Return topK results as array of objects with keys:
    //      "id", "title", "content", "score"
    // ------------------------------------------------------------------
    return [];
  }
}

// =============================================================================
// YOUR CODE: Hybrid Search with Reciprocal Rank Fusion
// =============================================================================

function hybridSearch(bm25Results, vectorResults, alpha = 0.5, k = 60) {
  /**
   * Combine BM25 and vector search results using Reciprocal Rank Fusion (RRF).
   *
   * RRF score = alpha * (1 / (k + rank_bm25)) + (1 - alpha) * (1 / (k + rank_vector))
   *
   * @param {Array} bm25Results - Results from BM25 search
   * @param {Array} vectorResults - Results from vector search
   * @param {number} alpha - Weight for BM25 vs vector (0.5 = equal weight)
   * @param {number} k - RRF constant (default 60, standard value)
   * @returns {Array} Combined results sorted by RRF score
   */
  // ------------------------------------------------------------------
  // TODO 5: Implement reciprocal rank fusion
  //   1. Build a map of docId -> { bm25Rank, vectorRank }
  //      Default rank for missing docs = 1000 (very low rank)
  //   2. For each docId, compute:
  //      rrfScore = alpha * (1/(k + bm25Rank)) + (1-alpha) * (1/(k + vectorRank))
  //   3. Sort by rrfScore descending
  //   4. Return array of objects with "id", "title", "content", "score" (= rrfScore),
  //      "bm25Rank", "vectorRank"
  //
  // Hint: Collect all unique doc IDs from both result sets. Use a Map
  // to store the full document info (title, content) from whichever
  // result set has it.
  // ------------------------------------------------------------------
  return [];
}

// =============================================================================
// MAIN (complete -- do not modify)
// =============================================================================

console.log("=".repeat(60));
console.log("M10 Lab - Step 1: Hybrid Search (BM25 + Vector)");
console.log("=".repeat(60));

// Setup
const collection = await setupChromaDB();
const bm25Index = new BM25Index(UCC_DOCUMENTS);

// Test queries -- each demonstrates different strengths
const testQueries = [
  ["UCC-3 amendment", "keyword wins -- exact term match"],
  ["How do I protect my loan?", "semantic wins -- concept match to 'perfection'"],
  ["filing expiration", "both work -- overlapping coverage"],
  ["What happens when collateral is sold?", "semantic wins -- concept: proceeds"],
  ["Article 9 Section 315", "keyword wins -- exact reference"],
];

for (const [query, explanation] of testQueries) {
  observe("QUERY", `${query}  (${explanation})`);

  // BM25 (keyword) search
  const bm25Results = bm25Index.search(query, 5);
  printResults("BM25 (Keyword) Results", bm25Results);

  // Vector (semantic) search
  const vecResults = await vectorSearch(query, collection, 5);
  printResults("Vector (Semantic) Results", vecResults);

  // Hybrid search
  const hybridResults = hybridSearch(bm25Results, vecResults, 0.5);
  printResults("Hybrid (Fused) Results", hybridResults);

  // Compare
  if (bm25Results.length && vecResults.length && hybridResults.length) {
    console.log(`  BM25 top result:   ${bm25Results[0].title || "N/A"}`);
    console.log(`  Vector top result: ${vecResults[0].title || "N/A"}`);
    console.log(`  Hybrid top result: ${hybridResults[0].title || "N/A"}`);
  }
  console.log();
}
