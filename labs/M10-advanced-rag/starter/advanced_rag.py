"""
M10 Lab - Step 3: Full Advanced RAG Pipeline (Starter)
======================================================
Build a complete advanced RAG pipeline with query transformation
(HyDE + multi-query), hybrid search, re-ranking, and generation.
Compare naive vs advanced RAG on UCC domain questions.

KEY CONCEPT: Advanced RAG improves EVERY stage of the pipeline:
  1. Query transformation -- rewrite queries for better retrieval
  2. Hybrid retrieval -- combine keyword + semantic search
  3. Re-ranking -- use Claude to sort by true relevance
  4. Generation -- answer with better context = better answers

Prerequisites:
    pip install anthropic python-dotenv chromadb

Usage:
    python advanced_rag.py
"""

import json
import math
import re
from dotenv import load_dotenv

load_dotenv()

import anthropic
import chromadb

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-20250514"


# =============================================================================
# UCC DOCUMENT CORPUS (complete -- do not modify)
# =============================================================================

UCC_DOCUMENTS = [
    {
        "id": "ucc-1",
        "title": "UCC-1 Financing Statement Overview",
        "content": (
            "A UCC-1 financing statement is a legal form that a creditor files to give "
            "notice that it has an interest in the personal property of a debtor. Filing a "
            "UCC-1 is the primary method of perfecting a security interest under Article 9 "
            "of the Uniform Commercial Code. The filing is made with the Secretary of State "
            "in the state where the debtor is organized. A UCC-1 filing is effective for "
            "five years from the date of filing and must be renewed by filing a continuation "
            "statement (UCC-3) before expiration."
        ),
    },
    {
        "id": "ucc-2",
        "title": "UCC-3 Amendment and Continuation",
        "content": (
            "A UCC-3 financing statement amendment is used to amend, assign, continue, or "
            "terminate a UCC-1 filing. A continuation statement must be filed within six "
            "months before the expiration of the original UCC-1 to keep the filing active. "
            "If a continuation is not filed, the UCC-1 lapses and the secured party loses "
            "its perfected status. The UCC-3 form can also be used to amend the collateral "
            "description, change the debtor or secured party name, or assign the security "
            "interest to a new party."
        ),
    },
    {
        "id": "ucc-3",
        "title": "Perfection of Security Interests",
        "content": (
            "Perfection is the process by which a secured party protects its security "
            "interest against claims of other creditors. The most common method of "
            "perfection is filing a UCC-1 financing statement. Other methods include "
            "taking possession of the collateral or obtaining control over deposit "
            "accounts, investment property, or letter-of-credit rights. A perfected "
            "security interest has priority over unperfected interests and over later-filed "
            "perfected interests. The rules of priority are set forth in Article 9, "
            "Section 9-322 of the UCC."
        ),
    },
    {
        "id": "ucc-4",
        "title": "Collateral Types and Descriptions",
        "content": (
            "Article 9 of the UCC covers security interests in personal property. "
            "Collateral types include goods (inventory, equipment, farm products, consumer "
            "goods), accounts receivable, chattel paper, deposit accounts, general "
            "intangibles (including payment intangibles and software), instruments, "
            "investment property, and letter-of-credit rights. The financing statement must "
            "describe the collateral, either by specific listing or by UCC type. A "
            "super-generic description like 'all assets' is permitted in financing "
            "statements but not in security agreements."
        ),
    },
    {
        "id": "ucc-5",
        "title": "Proceeds and After-Acquired Property",
        "content": (
            "When collateral is sold, exchanged, or otherwise disposed of, the secured "
            "party's interest automatically attaches to the proceeds. Proceeds include "
            "whatever is received upon the sale, lease, license, exchange, or other "
            "disposition of collateral. Cash proceeds and non-cash proceeds are treated "
            "differently under Article 9. The security interest in proceeds is "
            "automatically perfected for 20 days; to maintain perfection beyond that, the "
            "secured party must take additional steps. After-acquired property clauses "
            "allow a security interest to attach to property the debtor acquires after "
            "the security agreement is executed."
        ),
    },
    {
        "id": "ucc-6",
        "title": "Filing Office Rules and Procedures",
        "content": (
            "UCC filings are made with the appropriate filing office, typically the "
            "Secretary of State. The filing office must accept or reject a filing within "
            "prescribed time limits. Common reasons for rejection include failure to "
            "provide the debtor name, failure to provide the secured party name, or "
            "failure to pay the filing fee. Electronic filing (e-filing) is available in "
            "most jurisdictions and is the preferred method. Search logic varies by state, "
            "but most use a standard search algorithm that ignores case, punctuation, and "
            "common words (noise words) when matching debtor names."
        ),
    },
    {
        "id": "ucc-7",
        "title": "Article 9 Section 9-315: Proceeds and Priority",
        "content": (
            "Section 9-315 of Article 9 governs the disposition of collateral and the "
            "treatment of proceeds. Under 9-315(a)(1), a security interest continues in "
            "collateral notwithstanding sale, lease, license, exchange, or other "
            "disposition unless the secured party authorized the disposition free of the "
            "security interest. Under 9-315(a)(2), a security interest attaches to any "
            "identifiable proceeds of collateral. The 20-day automatic perfection rule "
            "for proceeds is found in 9-315(c) and (d). This section is critical for "
            "understanding how security interests follow collateral through various "
            "transactions."
        ),
    },
    {
        "id": "ucc-8",
        "title": "Debtor Name Requirements",
        "content": (
            "The debtor name on a UCC-1 financing statement must be exact. For registered "
            "organizations (corporations, LLCs), the name must match the name on the "
            "public organic record (e.g., articles of incorporation). For individuals, "
            "states vary between requiring the name on a driver's license (the 'only if' "
            "approach) or allowing the individual's legal name. An error in the debtor "
            "name that makes the filing seriously misleading renders the filing ineffective. "
            "The standard search logic test is used to determine if an error is seriously "
            "misleading."
        ),
    },
    {
        "id": "ucc-9",
        "title": "Priority Rules and Lien Positions",
        "content": (
            "Priority among competing security interests is generally determined by the "
            "order of filing or perfection (first-in-time, first-in-right). A perfected "
            "security interest has priority over an unperfected one. A purchase money "
            "security interest (PMSI) in goods other than inventory has priority over a "
            "conflicting security interest if perfected within 20 days of delivery. For "
            "inventory PMSIs, the secured party must also send notification to holders of "
            "conflicting security interests. Lien creditors (including bankruptcy trustees) "
            "take priority over unperfected security interests."
        ),
    },
    {
        "id": "ucc-10",
        "title": "Termination and Release",
        "content": (
            "When the debtor has fulfilled all obligations under the security agreement, "
            "the secured party must file a UCC-3 termination statement within 20 days of "
            "receiving an authenticated demand from the debtor. For consumer goods, the "
            "secured party must file a termination within one month of the obligation being "
            "fulfilled or within 20 days of receiving a demand. Failure to file a "
            "termination statement can result in liability for the secured party, including "
            "actual damages and a statutory penalty of $500 per violation. The termination "
            "extinguishes the effectiveness of the financing statement."
        ),
    },
]


# =============================================================================
# INFRASTRUCTURE (complete -- do not modify)
# Hybrid search, BM25, ChromaDB, vector search, re-ranking
# =============================================================================

def setup_chromadb():
    """Create an in-memory ChromaDB collection with UCC documents."""
    chroma_client = chromadb.Client()
    try:
        chroma_client.delete_collection("ucc_documents_advanced")
    except Exception:
        pass

    collection = chroma_client.create_collection(
        name="ucc_documents_advanced",
        metadata={"hnsw:space": "cosine"},
    )
    collection.add(
        ids=[doc["id"] for doc in UCC_DOCUMENTS],
        documents=[doc["content"] for doc in UCC_DOCUMENTS],
        metadatas=[{"title": doc["title"]} for doc in UCC_DOCUMENTS],
    )
    return collection


class BM25Index:
    """Minimal BM25 implementation."""

    def __init__(self, documents, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.documents = documents
        self.doc_count = len(documents)
        self.doc_tokens = [re.findall(r'\w+', doc["content"].lower()) for doc in documents]
        self.doc_lengths = [len(t) for t in self.doc_tokens]
        self.avg_doc_length = sum(self.doc_lengths) / self.doc_count if self.doc_count > 0 else 0
        self.df = {}
        for tokens in self.doc_tokens:
            for term in set(tokens):
                self.df[term] = self.df.get(term, 0) + 1

    def search(self, query, top_k=5):
        query_tokens = re.findall(r'\w+', query.lower())
        scores = []
        for i in range(self.doc_count):
            score = 0.0
            dl = self.doc_lengths[i]
            for token in query_tokens:
                tf = self.doc_tokens[i].count(token)
                df = self.df.get(token, 0)
                idf = math.log((self.doc_count - df + 0.5) / (df + 0.5) + 1)
                score += idf * (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * dl / self.avg_doc_length))
            scores.append((i, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return [
            {"id": self.documents[i]["id"], "title": self.documents[i]["title"],
             "content": self.documents[i]["content"], "score": s}
            for i, s in scores[:top_k]
        ]


def vector_search(query, collection, top_k=5):
    """Semantic search using ChromaDB."""
    results = collection.query(query_texts=[query], n_results=top_k)
    return [
        {"id": results["ids"][0][i], "content": results["documents"][0][i],
         "title": results["metadatas"][0][i]["title"],
         "score": 1 - results["distances"][0][i]}
        for i in range(len(results["ids"][0]))
    ]


def hybrid_search_fusion(bm25_results, vector_results, alpha=0.5, k=60):
    """Reciprocal rank fusion."""
    doc_info = {}
    bm25_ranks = {}
    vector_ranks = {}

    for rank, r in enumerate(bm25_results, 1):
        bm25_ranks[r["id"]] = rank
        doc_info[r["id"]] = {"title": r["title"], "content": r["content"]}
    for rank, r in enumerate(vector_results, 1):
        vector_ranks[r["id"]] = rank
        doc_info[r["id"]] = {"title": r["title"], "content": r["content"]}

    all_ids = set(list(bm25_ranks.keys()) + list(vector_ranks.keys()))
    fused = []
    for doc_id in all_ids:
        br = bm25_ranks.get(doc_id, 1000)
        vr = vector_ranks.get(doc_id, 1000)
        rrf_score = alpha * (1 / (k + br)) + (1 - alpha) * (1 / (k + vr))
        info = doc_info[doc_id]
        fused.append({"id": doc_id, "title": info["title"], "content": info["content"], "score": rrf_score})
    fused.sort(key=lambda x: x["score"], reverse=True)
    return fused


def rerank_with_claude(query, candidates, top_k=3):
    """Re-rank candidates using Claude as a cross-encoder."""
    scored = []
    for candidate in candidates:
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=200,
                system=(
                    "Rate the relevance of this passage to the query on a scale of 0-10. "
                    'Return ONLY a JSON object: {"score": N, "reason": "..."}'
                ),
                messages=[{
                    "role": "user",
                    "content": f"Query: {query}\n\nPassage: {candidate['content']}",
                }],
            )
            text = response.content[0].text.strip()
            data = json.loads(text)
            scored.append({"candidate": candidate, "score": data.get("score", 0), "reason": data.get("reason", "")})
        except Exception:
            scored.append({"candidate": candidate, "score": 0, "reason": "Error scoring"})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return [s["candidate"] for s in scored[:top_k]]


# =============================================================================
# NAIVE RAG (complete -- do not modify)
# =============================================================================

def naive_rag(query, collection):
    """
    Simple naive RAG: vector search -> top 3 results -> generate answer.
    This is the baseline we are trying to beat.
    """
    # Retrieve
    results = vector_search(query, collection, top_k=3)
    context = "\n\n".join([f"[{r['title']}]\n{r['content']}" for r in results])

    # Generate
    response = client.messages.create(
        model=MODEL,
        max_tokens=500,
        system=(
            "You are a UCC (Uniform Commercial Code) expert. Answer the question based "
            "ONLY on the provided context. If the context doesn't contain the answer, say so."
        ),
        messages=[{
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {query}",
        }],
    )

    return {
        "answer": response.content[0].text,
        "sources": [r["title"] for r in results],
    }


# =============================================================================
# OBSERVATION HELPERS (complete -- do not modify)
# =============================================================================

def observe(label, message):
    print(f"\n{'=' * 60}")
    print(f"[{label}] {message}")
    print(f"{'=' * 60}")


def observe_step(step, message):
    print(f"\n  [{step}] {message}")


# =============================================================================
# YOUR CODE: Query Transformations
# =============================================================================

def transform_query_hyde(query):
    """
    HyDE (Hypothetical Document Embedding): Ask Claude to write a hypothetical
    answer to the query. Use that hypothetical answer as the search query instead
    of the original question.

    WHY: The hypothetical answer is closer in embedding space to the actual
    documents than the question is.

    Args:
        query: The original user question

    Returns:
        The hypothetical document text to use for retrieval
    """
    observe_step("HyDE", f"Generating hypothetical answer for: {query}")

    # ------------------------------------------------------------------
    # TODO 1: Implement HyDE query transformation
    #   Call Claude with:
    #     - system: "Write a short paragraph that would be a perfect answer
    #       to this question about UCC (Uniform Commercial Code) law.
    #       Write as if you are quoting from a legal textbook.
    #       Do NOT say 'based on the context' -- just write the answer directly."
    #     - messages: [{"role": "user", "content": query}]
    #     - model=MODEL, max_tokens=300
    #   Return the text of Claude's response.
    # ------------------------------------------------------------------
    return query  # Fallback: return original query


def transform_query_multi(query):
    """
    Multi-Query: Generate 3 different search queries from different angles
    to cast a wider retrieval net.

    WHY: A single query may miss relevant documents that use different
    terminology. Multiple queries from different angles catch more.

    Args:
        query: The original user question

    Returns:
        List of 3 alternative search queries
    """
    observe_step("MULTI-QUERY", f"Generating alternative queries for: {query}")

    # ------------------------------------------------------------------
    # TODO 2: Implement multi-query transformation
    #   Call Claude with:
    #     - system: "Generate exactly 3 different search queries that would
    #       help answer the user's question about UCC law. Each query should
    #       approach the topic from a different angle or use different
    #       terminology. Return ONLY a JSON array of 3 strings."
    #     - messages: [{"role": "user", "content": query}]
    #     - model=MODEL, max_tokens=300
    #   Parse the JSON array and return it.
    #   Handle errors by returning [query] (the original query).
    # ------------------------------------------------------------------
    return [query]  # Fallback: return original query


# =============================================================================
# YOUR CODE: Advanced RAG Pipeline
# =============================================================================

def advanced_rag_pipeline(query, collection, bm25_index):
    """
    Full advanced RAG pipeline:
      1. Transform the query (HyDE + multi-query)
      2. Hybrid search (BM25 + vector) using ALL transformed queries
      3. Deduplicate and re-rank with Claude
      4. Generate final answer

    Args:
        query: The original user question
        collection: ChromaDB collection
        bm25_index: BM25Index instance

    Returns:
        dict with "answer", "sources", "hyde_query", "multi_queries"
    """
    observe_step("PIPELINE", "Starting advanced RAG pipeline")

    # ------------------------------------------------------------------
    # TODO 3: Implement the full advanced RAG pipeline
    #
    # Step 1: Query transformation
    #   hyde_query = transform_query_hyde(query)
    #   multi_queries = transform_query_multi(query)
    #   all_queries = [query, hyde_query] + multi_queries
    #
    # Step 2: Hybrid search with ALL queries
    #   Collect results from hybrid search for each query.
    #   For each q in all_queries:
    #     bm25_results = bm25_index.search(q, top_k=5)
    #     vec_results = vector_search(q, collection, top_k=5)
    #     fused = hybrid_search_fusion(bm25_results, vec_results)
    #     Add fused results to a master list
    #
    # Step 3: Deduplicate by doc ID (keep the one with highest score)
    #   Build a dict: doc_id -> best result
    #   Convert back to a sorted list
    #
    # Step 4: Re-rank top candidates with Claude
    #   top_candidates = rerank_with_claude(query, deduped[:7], top_k=3)
    #
    # Step 5: Generate final answer
    #   Build context from top_candidates
    #   Call Claude with the same system prompt as naive_rag
    #   Return dict with "answer", "sources", "hyde_query", "multi_queries"
    # ------------------------------------------------------------------
    return {
        "answer": "Not implemented yet",
        "sources": [],
        "hyde_query": "",
        "multi_queries": [],
    }


# =============================================================================
# YOUR CODE: Compare Naive vs Advanced
# =============================================================================

def compare_naive_vs_advanced(query, collection, bm25_index):
    """
    Run both naive and advanced RAG on the same query and show comparison.

    Args:
        query: The user question
        collection: ChromaDB collection
        bm25_index: BM25Index instance

    Returns:
        dict with "query", "naive", "advanced"
    """
    # ------------------------------------------------------------------
    # TODO 4: Run both pipelines and return comparison
    #   naive_result = naive_rag(query, collection)
    #   advanced_result = advanced_rag_pipeline(query, collection, bm25_index)
    #   Return {"query": query, "naive": naive_result, "advanced": advanced_result}
    # ------------------------------------------------------------------
    return {
        "query": query,
        "naive": {"answer": "Not implemented", "sources": []},
        "advanced": {"answer": "Not implemented", "sources": [], "hyde_query": "", "multi_queries": []},
    }


# =============================================================================
# MAIN (complete -- do not modify)
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M10 Lab - Step 3: Full Advanced RAG Pipeline")
    print("=" * 60)

    # Setup
    collection = setup_chromadb()
    bm25_index = BM25Index(UCC_DOCUMENTS)

    # Test queries -- UCC domain questions
    test_queries = [
        "What happens if I forget to renew my UCC filing?",
        "How do I get first priority on a loan secured by inventory?",
        "Can a security interest follow collateral that gets sold?",
        "What are the requirements for the debtor name on a financing statement?",
        "How do I release a UCC lien after the loan is paid off?",
    ]

    # Run comparison for each query
    print("\n" + "=" * 100)
    print(f"{'QUERY':<50} | {'NAIVE RAG':<25} | {'ADVANCED RAG':<25}")
    print("=" * 100)

    for query in test_queries:
        observe("COMPARING", query)

        result = compare_naive_vs_advanced(query, collection, bm25_index)

        # Print naive result
        print(f"\n  NAIVE RAG:")
        print(f"    Sources: {', '.join(result['naive']['sources'])}")
        print(f"    Answer:  {result['naive']['answer'][:200]}...")

        # Print advanced result
        print(f"\n  ADVANCED RAG:")
        if result["advanced"].get("hyde_query"):
            print(f"    HyDE query: {result['advanced']['hyde_query'][:100]}...")
        if result["advanced"].get("multi_queries"):
            for i, q in enumerate(result["advanced"]["multi_queries"]):
                print(f"    Multi-query {i+1}: {q}")
        print(f"    Sources: {', '.join(result['advanced']['sources'])}")
        print(f"    Answer:  {result['advanced']['answer'][:200]}...")

        print(f"\n  {'─' * 80}")

    print("\n" + "=" * 60)
    print("Pipeline comparison complete!")
    print("=" * 60)
