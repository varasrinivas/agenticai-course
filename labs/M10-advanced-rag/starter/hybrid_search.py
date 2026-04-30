"""
M10 Lab - Step 1: Hybrid Search (Starter)
==========================================
Build hybrid search combining BM25 keyword search with vector semantic
search using reciprocal rank fusion.

KEY CONCEPT: Keyword search (BM25) excels at exact term matching.
Semantic search (vectors) excels at concept matching. Hybrid search
combines both to get the best of both worlds.

Prerequisites:
    pip install anthropic python-dotenv chromadb rank-bm25

Usage:
    python hybrid_search.py
"""

import json
import math
import re
from dotenv import load_dotenv

load_dotenv()

import anthropic
import chromadb

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"


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
# CHROMADB SETUP (complete -- do not modify)
# =============================================================================

def setup_chromadb():
    """Create an in-memory ChromaDB collection with UCC documents."""
    chroma_client = chromadb.Client()

    # Delete collection if it exists (for reruns)
    try:
        chroma_client.delete_collection("ucc_documents")
    except Exception:
        pass

    collection = chroma_client.create_collection(
        name="ucc_documents",
        metadata={"hnsw:space": "cosine"},
    )

    collection.add(
        ids=[doc["id"] for doc in UCC_DOCUMENTS],
        documents=[doc["content"] for doc in UCC_DOCUMENTS],
        metadatas=[{"title": doc["title"]} for doc in UCC_DOCUMENTS],
    )

    return collection


# =============================================================================
# VECTOR SEARCH (complete -- do not modify)
# =============================================================================

def vector_search(query, collection, top_k=5):
    """Semantic search using ChromaDB's built-in embedding."""
    results = collection.query(query_texts=[query], n_results=top_k)

    search_results = []
    for i in range(len(results["ids"][0])):
        search_results.append({
            "id": results["ids"][0][i],
            "content": results["documents"][0][i],
            "title": results["metadatas"][0][i]["title"],
            "distance": results["distances"][0][i],
            "score": 1 - results["distances"][0][i],  # Convert distance to similarity
        })

    return search_results


# =============================================================================
# OBSERVATION HELPERS (complete -- do not modify)
# =============================================================================

def observe(label, message):
    """Print a labeled observation line."""
    print(f"\n{'=' * 60}")
    print(f"[{label}] {message}")
    print(f"{'=' * 60}")


def print_results(label, results, max_display=5):
    """Print search results in a readable format."""
    print(f"\n--- {label} ---")
    for i, r in enumerate(results[:max_display]):
        score = r.get("score", 0)
        title = r.get("title", "Unknown")
        print(f"  {i+1}. [{score:.4f}] {title}")
        print(f"     {r['content'][:100]}...")
    print()


# =============================================================================
# YOUR CODE: BM25 Index
# =============================================================================

class BM25Index:
    """
    BM25 (Best Matching 25) is a ranking function used in information retrieval.
    It scores documents based on term frequency (TF) and inverse document
    frequency (IDF), with length normalization.

    Parameters:
        k1: Term frequency saturation parameter (default 1.5)
        b: Length normalization parameter (default 0.75)
    """

    def __init__(self, documents, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.documents = documents
        self.doc_count = len(documents)

        # Tokenize all documents
        self.doc_tokens = [self._tokenize(doc["content"]) for doc in documents]
        self.doc_lengths = [len(tokens) for tokens in self.doc_tokens]
        self.avg_doc_length = sum(self.doc_lengths) / self.doc_count if self.doc_count > 0 else 0

        # ------------------------------------------------------------------
        # TODO 1: Build the document frequency (DF) dictionary
        #   For each document's tokens, count how many documents contain
        #   each unique term. Store in self.df (dict: term -> count).
        #   Hint: Use a set for each document's tokens to avoid counting
        #   a term twice in the same document.
        # ------------------------------------------------------------------
        self.df = {}  # term -> number of documents containing the term
        pass

    def _tokenize(self, text):
        """Simple tokenizer: lowercase, split on non-alphanumeric characters."""
        return re.findall(r'\w+', text.lower())

    def _idf(self, term):
        """
        Compute Inverse Document Frequency for a term.
        IDF = ln((N - df + 0.5) / (df + 0.5) + 1)
        where N = total docs, df = docs containing term
        """
        # ------------------------------------------------------------------
        # TODO 2: Implement IDF calculation
        #   Use self.df to get the document frequency for the term.
        #   If the term is not in self.df, df = 0.
        #   Return: math.log((self.doc_count - df + 0.5) / (df + 0.5) + 1)
        # ------------------------------------------------------------------
        return 0.0

    def _score_document(self, query_tokens, doc_index):
        """
        Compute BM25 score for a single document given query tokens.
        Score = sum of IDF(term) * (TF * (k1+1)) / (TF + k1 * (1 - b + b * dl/avgdl))
        """
        # ------------------------------------------------------------------
        # TODO 3: Implement BM25 scoring for a single document
        #   For each query token:
        #     1. Get tf = count of token in self.doc_tokens[doc_index]
        #     2. Get idf = self._idf(token)
        #     3. Get dl = self.doc_lengths[doc_index]
        #     4. Compute: idf * (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * dl / self.avg_doc_length))
        #     5. Sum all terms
        # ------------------------------------------------------------------
        return 0.0

    def search(self, query, top_k=5):
        """Search documents using BM25 scoring."""
        query_tokens = self._tokenize(query)

        # ------------------------------------------------------------------
        # TODO 4: Score all documents and return top_k results
        #   1. For each document, compute _score_document(query_tokens, i)
        #   2. Sort by score descending
        #   3. Return top_k results as list of dicts with keys:
        #      "id", "title", "content", "score"
        # ------------------------------------------------------------------
        return []


# =============================================================================
# YOUR CODE: Hybrid Search with Reciprocal Rank Fusion
# =============================================================================

def hybrid_search(bm25_results, vector_results, alpha=0.5, k=60):
    """
    Combine BM25 and vector search results using Reciprocal Rank Fusion (RRF).

    RRF score = alpha * (1 / (k + rank_bm25)) + (1 - alpha) * (1 / (k + rank_vector))

    Args:
        bm25_results: Results from BM25 search (list of dicts with "id")
        vector_results: Results from vector search (list of dicts with "id")
        alpha: Weight for BM25 vs vector (0.5 = equal weight)
        k: RRF constant (default 60, standard value)

    Returns:
        Combined results sorted by RRF score
    """
    # ------------------------------------------------------------------
    # TODO 5: Implement reciprocal rank fusion
    #   1. Build a dict mapping doc_id -> {"bm25_rank": rank, "vector_rank": rank}
    #      Default rank for missing docs = 1000 (very low rank)
    #   2. For each doc_id, compute:
    #      rrf_score = alpha * (1/(k + bm25_rank)) + (1-alpha) * (1/(k + vector_rank))
    #   3. Sort by rrf_score descending
    #   4. Return list of dicts with "id", "title", "content", "score" (= rrf_score),
    #      "bm25_rank", "vector_rank"
    #
    # Hint: Collect all unique doc IDs from both result sets. Use a dict
    # to store the full document info (title, content) from whichever
    # result set has it.
    # ------------------------------------------------------------------
    return []


# =============================================================================
# MAIN (complete -- do not modify)
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("M10 Lab - Step 1: Hybrid Search (BM25 + Vector)")
    print("=" * 60)

    # Setup
    collection = setup_chromadb()
    bm25_index = BM25Index(UCC_DOCUMENTS)

    # Test queries -- each demonstrates different strengths
    test_queries = [
        ("UCC-3 amendment", "keyword wins -- exact term match"),
        ("How do I protect my loan?", "semantic wins -- concept match to 'perfection'"),
        ("filing expiration", "both work -- overlapping coverage"),
        ("What happens when collateral is sold?", "semantic wins -- concept: proceeds"),
        ("Article 9 Section 315", "keyword wins -- exact reference"),
    ]

    for query, explanation in test_queries:
        observe("QUERY", f"{query}  ({explanation})")

        # BM25 (keyword) search
        bm25_results = bm25_index.search(query, top_k=5)
        print_results("BM25 (Keyword) Results", bm25_results)

        # Vector (semantic) search
        vec_results = vector_search(query, collection, top_k=5)
        print_results("Vector (Semantic) Results", vec_results)

        # Hybrid search
        hybrid_results = hybrid_search(bm25_results, vec_results, alpha=0.5)
        print_results("Hybrid (Fused) Results", hybrid_results)

        # Compare: show which approach found the best result
        if bm25_results and vec_results and hybrid_results:
            print(f"  BM25 top result:   {bm25_results[0].get('title', 'N/A')}")
            print(f"  Vector top result: {vec_results[0].get('title', 'N/A')}")
            print(f"  Hybrid top result: {hybrid_results[0].get('title', 'N/A')}")
        print()
