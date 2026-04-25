/**
 * M10 Lab - Step 2: Re-Ranking with Claude (Solution)
 * ===================================================
 * Complete solution: retrieve broadly with hybrid search, then use
 * Claude to score and re-rank candidates by relevance.
 *
 * Prerequisites:
 *     npm install @anthropic-ai/sdk dotenv chromadb
 *
 * Usage:
 *     node reranker.js
 */

import Anthropic from "@anthropic-ai/sdk";
import { ChromaClient } from "chromadb";
import "dotenv/config";

const client = new Anthropic();
const MODEL = "claude-sonnet-4-20250514";

// =============================================================================
// UCC DOCUMENT CORPUS
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
// INFRASTRUCTURE
// =============================================================================

async function setupChromaDB() {
  const chromaClient = new ChromaClient();
  try {
    await chromaClient.deleteCollection({ name: "ucc_documents_reranker" });
  } catch (e) {
    // Ignore
  }
  const collection = await chromaClient.createCollection({
    name: "ucc_documents_reranker",
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

function hybridSearch(bm25Results, vectorResults, alpha = 0.5, k = 60) {
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

async function retrieveCandidates(query, collection, bm25Index, n = 10) {
  const bm25Results = bm25Index.search(query, n);
  const vecResults = await vectorSearch(query, collection, n);
  const candidates = hybridSearch(bm25Results, vecResults, 0.5);
  return candidates.slice(0, n);
}

// =============================================================================
// OBSERVATION HELPERS
// =============================================================================

function observe(label, message) {
  console.log(`\n${"=".repeat(60)}`);
  console.log(`[${label}] ${message}`);
  console.log("=".repeat(60));
}

function printRankedResults(label, results, scores = null) {
  console.log(`\n--- ${label} ---`);
  for (let i = 0; i < results.length; i++) {
    const r = results[i];
    const title = r.title || "Unknown";
    let relevance = "";
    if (scores && i < scores.length) {
      relevance = ` | Claude score: ${scores[i].score}/10 -- ${scores[i].reason}`;
    }
    console.log(`  ${i + 1}. ${title}${relevance}`);
    console.log(`     ${r.content.slice(0, 80)}...`);
  }
  console.log();
}

// =============================================================================
// SOLUTION: Re-ranking with Claude
// =============================================================================

const RERANK_PROMPT =
  'Rate the relevance of this passage to the query on a scale of 0-10. ' +
  'Return ONLY a JSON object: {"score": N, "reason": "..."}';

async function rerankWithClaude(query, candidates) {
  const scores = [];

  for (const candidate of candidates) {
    try {
      const response = await client.messages.create({
        model: MODEL,
        max_tokens: 200,
        system: RERANK_PROMPT,
        messages: [
          {
            role: "user",
            content: `Query: ${query}\n\nPassage: ${candidate.content}`,
          },
        ],
      });

      let text = response.content[0].text.trim();
      // Handle potential markdown code blocks
      if (text.startsWith("```")) {
        text = text.split("\n").slice(1).join("\n").replace(/```$/, "").trim();
      }
      const data = JSON.parse(text);
      scores.push({
        score: data.score || 0,
        reason: data.reason || "No reason provided",
      });
    } catch (e) {
      scores.push({ score: 0, reason: `Error parsing response: ${e.message}` });
    }
  }

  return scores;
}

function rerank(query, candidates, scores, topK = 3) {
  // Pair candidates with scores
  const paired = candidates.map((c, i) => ({ candidate: c, score: scores[i] }));

  // Sort by score descending
  paired.sort((a, b) => b.score.score - a.score.score);

  // Split back and take topK
  const rerankedCandidates = paired.slice(0, topK).map((p) => p.candidate);
  const rerankedScores = paired.slice(0, topK).map((p) => p.score);

  return [rerankedCandidates, rerankedScores];
}

// =============================================================================
// MAIN
// =============================================================================

console.log("=".repeat(60));
console.log("M10 Lab - Step 2: Re-Ranking with Claude (SOLUTION)");
console.log("=".repeat(60));

const collection = await setupChromaDB();
const bm25Index = new BM25Index(UCC_DOCUMENTS);

const testQueries = [
  "What are the consequences of not filing a continuation statement?",
  "How does a lender establish first-priority position?",
  "What happens to a security interest when the debtor sells the collateral?",
];

for (const query of testQueries) {
  observe("QUERY", query);

  const candidates = await retrieveCandidates(query, collection, bm25Index, 7);
  printRankedResults("BEFORE Re-Ranking (Hybrid Search Order)", candidates);

  const scores = await rerankWithClaude(query, candidates);

  const [reranked, rerankedScores] = rerank(query, candidates, scores, 3);
  printRankedResults("AFTER Re-Ranking (Claude-Scored)", reranked, rerankedScores);

  if (reranked.length && candidates.length) {
    console.log("  Re-ranking changes:");
    for (let i = 0; i < reranked.length; i++) {
      const doc = reranked[i];
      const originalPos =
        candidates.findIndex((c) => c.id === doc.id) + 1 || "?";
      console.log(`    #${i + 1} was #${originalPos}: ${doc.title}`);
    }
  }
  console.log();
}
