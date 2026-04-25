"""
M22B — Mock UCC Agent (Complete — do not modify)
===================================================
Provides a MockUCCAgent that returns realistic responses
WITHOUT requiring an Anthropic API key. This lets you test
the entire deployment pipeline (Docker, GCP, AWS) locally.

The mock data is imported from M15B's mock_data module,
but we embed a local copy here so M22B is self-contained.
"""

import json
import time
from typing import Generator


# ---------------------------------------------------------------------------
# Embedded mock data (subset from M15B)
# ---------------------------------------------------------------------------

MOCK_FILINGS = [
    {
        "filing_number": "UCC-2024-NY-0012847",
        "type": "UCC-1",
        "state": "New York",
        "filing_date": "2024-03-15",
        "expiration_date": "2029-03-15",
        "status": "Active",
        "debtor": {
            "name": "Acme Corporation",
            "address": "450 West 33rd Street, Suite 800, New York, NY 10001",
            "org_type": "Corporation",
            "jurisdiction": "New York",
        },
        "secured_party": {
            "name": "Atlantic Capital Partners",
            "address": "1 Chase Manhattan Plaza, Floor 45, New York, NY 10005",
        },
        "collateral_description": (
            "All accounts receivable, inventory, equipment, and general "
            "intangibles now owned or hereafter acquired by Debtor."
        ),
    },
    {
        "filing_number": "UCC-2024-NY-0015921",
        "type": "UCC-1",
        "state": "New York",
        "filing_date": "2024-05-22",
        "expiration_date": "2029-05-22",
        "status": "Active",
        "debtor": {
            "name": "Acme Corporation",
            "address": "450 West 33rd Street, Suite 800, New York, NY 10001",
            "org_type": "Corporation",
            "jurisdiction": "New York",
        },
        "secured_party": {
            "name": "Citibank N.A.",
            "address": "388 Greenwich Street, New York, NY 10013",
        },
        "collateral_description": (
            "All deposit accounts, investment property, and letter-of-credit "
            "rights held at or through Citibank."
        ),
    },
    {
        "filing_number": "UCC-2024-CA-0101457",
        "type": "UCC-1",
        "state": "California",
        "filing_date": "2024-04-03",
        "expiration_date": "2029-04-03",
        "status": "Active",
        "debtor": {
            "name": "Acme Corporation",
            "address": "100 California Street, Suite 2000, San Francisco, CA 94111",
            "org_type": "Corporation",
            "jurisdiction": "New York",
        },
        "secured_party": {
            "name": "Bank of America N.A.",
            "address": "555 California Street, San Francisco, CA 94104",
        },
        "collateral_description": (
            "All equipment and fixtures located at debtor's San Francisco "
            "and Los Angeles offices."
        ),
    },
    {
        "filing_number": "UCC-2024-TX-0201337",
        "type": "UCC-1",
        "state": "Texas",
        "filing_date": "2024-02-28",
        "expiration_date": "2029-02-28",
        "status": "Active",
        "debtor": {
            "name": "Acme Corporation",
            "address": "2001 Ross Avenue, Suite 700, Dallas, TX 75201",
            "org_type": "Corporation",
            "jurisdiction": "New York",
        },
        "secured_party": {
            "name": "PNC Bank N.A.",
            "address": "300 Fifth Avenue, Pittsburgh, PA 15222",
        },
        "collateral_description": (
            "All accounts receivable and contract rights arising from "
            "debtor's Texas operations."
        ),
    },
    {
        "filing_number": "UCC-2024-FL-0059811",
        "type": "UCC-1",
        "state": "Florida",
        "filing_date": "2024-07-20",
        "expiration_date": "2029-07-20",
        "status": "Active",
        "debtor": {
            "name": "Acme Corporation",
            "address": "1395 Brickell Avenue, Suite 800, Miami, FL 33131",
            "org_type": "Corporation",
            "jurisdiction": "New York",
        },
        "secured_party": {
            "name": "Atlantic Capital Partners",
            "address": "1 Chase Manhattan Plaza, Floor 45, New York, NY 10005",
        },
        "collateral_description": (
            "All accounts receivable, inventory, and general intangibles "
            "of debtor's Florida division."
        ),
    },
    {
        "filing_number": "UCC-2024-IL-0081290",
        "type": "UCC-1",
        "state": "Illinois",
        "filing_date": "2024-04-30",
        "expiration_date": "2029-04-30",
        "status": "Active",
        "debtor": {
            "name": "Acme Corporation",
            "address": "233 S Wacker Drive, Suite 4500, Chicago, IL 60606",
            "org_type": "Corporation",
            "jurisdiction": "New York",
        },
        "secured_party": {
            "name": "JPMorgan Chase Bank N.A.",
            "address": "383 Madison Avenue, New York, NY 10179",
        },
        "collateral_description": (
            "All assets of debtor's Illinois subsidiary including accounts, "
            "inventory, equipment, and all proceeds thereof."
        ),
    },
    {
        "filing_number": "UCC-2024-NY-0019004",
        "type": "UCC-1",
        "state": "New York",
        "filing_date": "2024-08-10",
        "expiration_date": "2029-08-10",
        "status": "Active",
        "debtor": {
            "name": "Greenfield Logistics LLC",
            "address": "200 Park Avenue, Suite 1500, New York, NY 10166",
            "org_type": "LLC",
            "jurisdiction": "New York",
        },
        "secured_party": {
            "name": "JPMorgan Chase Bank N.A.",
            "address": "383 Madison Avenue, New York, NY 10179",
        },
        "collateral_description": (
            "All inventory held at debtor's warehouse facilities in New York "
            "State; all accounts receivable arising from distribution operations."
        ),
    },
    {
        "filing_number": "UCC-2023-TX-0187634",
        "type": "UCC-1",
        "state": "Texas",
        "filing_date": "2023-09-10",
        "expiration_date": "2028-09-10",
        "status": "Active",
        "debtor": {
            "name": "Lone Star Energy Solutions LP",
            "address": "1200 Smith Street, Suite 3000, Houston, TX 77002",
            "org_type": "Limited Partnership",
            "jurisdiction": "Texas",
        },
        "secured_party": {
            "name": "Wells Fargo Equipment Finance",
            "address": "301 South College Street, Charlotte, NC 28202",
        },
        "collateral_description": (
            "Specific equipment: (3) Caterpillar 349F L hydraulic excavators, "
            "serial numbers CAT349F-8821, CAT349F-8822, CAT349F-8823; "
            "(1) Liebherr LTM 1300-6.2 mobile crane, serial number LTM-DE-90124."
        ),
    },
]


def _search_filings(
    debtor_name: str | None = None,
    state: str | None = None,
    max_results: int = 10,
) -> list[dict]:
    """Search mock filings by debtor name and/or state."""
    results = MOCK_FILINGS
    if debtor_name:
        results = [
            f for f in results
            if debtor_name.lower() in f["debtor"]["name"].lower()
        ]
    if state:
        results = [
            f for f in results
            if f["state"].lower() == state.lower()
        ]
    return results[:max_results]


def _calculate_risk(filings: list[dict]) -> dict:
    """Calculate a mock risk score from a list of filings."""
    if not filings:
        return {
            "risk_score": 0.0,
            "risk_level": "Low",
            "total_liens": 0,
            "states_with_filings": 0,
            "recommendation": "No filings found. Low risk by default.",
        }

    total = len(filings)
    states = len(set(f["state"] for f in filings))
    blanket = sum(
        1 for f in filings
        if any(kw in f["collateral_description"].lower()
               for kw in ["all assets", "all accounts", "general intangibles"])
    )

    # Simple scoring: base + per-filing + per-state + blanket penalty
    score = min(100.0, 15.0 + total * 10.0 + states * 5.0 + blanket * 8.0)

    if score >= 75:
        level = "High"
        rec = "Significant lien exposure across multiple jurisdictions. Conduct detailed due diligence before extending credit."
    elif score >= 45:
        level = "Medium"
        rec = "Moderate lien exposure. Review collateral overlap and secured party concentration."
    else:
        level = "Low"
        rec = "Limited lien exposure. Standard monitoring recommended."

    return {
        "risk_score": round(score, 1),
        "risk_level": level,
        "total_liens": total,
        "states_with_filings": states,
        "recommendation": rec,
    }


def _format_filing_summary(filing: dict) -> dict:
    """Convert a raw filing to a FilingSummary-compatible dict."""
    collateral = filing["collateral_description"]
    if len(collateral) > 120:
        collateral = collateral[:117] + "..."
    return {
        "filing_number": filing["filing_number"],
        "filing_type": filing["type"],
        "state": filing["state"],
        "status": filing["status"],
        "debtor_name": filing["debtor"]["name"],
        "secured_party_name": filing["secured_party"]["name"],
        "filing_date": filing["filing_date"],
        "collateral_summary": collateral,
    }


class MockUCCAgent:
    """
    Mock agent that mimics the M15B UCC Filing Research Agent
    without calling the Anthropic API.

    Supports:
    - query(query, state, include_risk, max_results) -> dict
    - query_stream(query, state, include_risk, max_results) -> Generator[str]
    """

    def query(
        self,
        query: str,
        state: str | None = None,
        include_risk: bool = False,
        max_results: int = 10,
    ) -> dict:
        """Process a query synchronously and return a structured response."""
        start = time.time()

        # Extract debtor name from query (simple heuristic)
        debtor_name = self._extract_debtor(query)

        # Search filings
        filings = _search_filings(
            debtor_name=debtor_name,
            state=state or self._extract_state(query),
            max_results=max_results,
        )

        # Build answer text
        filing_summaries = [_format_filing_summary(f) for f in filings]
        answer = self._build_answer(debtor_name, filings, state)

        # Risk analysis (if requested or if query mentions risk)
        risk = None
        if include_risk or self._mentions_risk(query):
            risk = _calculate_risk(filings)

        elapsed = (time.time() - start) * 1000
        return {
            "answer": answer,
            "filings": filing_summaries,
            "risk": risk,
            "processing_time_ms": round(elapsed, 2),
        }

    def query_stream(
        self,
        query: str,
        state: str | None = None,
        include_risk: bool = False,
        max_results: int = 10,
    ) -> Generator[str, None, None]:
        """Process a query and yield SSE-formatted chunks."""
        debtor_name = self._extract_debtor(query)
        filings = _search_filings(
            debtor_name=debtor_name,
            state=state or self._extract_state(query),
            max_results=max_results,
        )

        # Stream the answer in chunks
        answer = self._build_answer(debtor_name, filings, state)
        words = answer.split()
        chunk_size = 5
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i : i + chunk_size])
            yield f"event: chunk\ndata: {json.dumps({'text': chunk})}\n\n"
            time.sleep(0.05)  # Simulate streaming delay

        # Stream filing summaries
        for filing in filings:
            summary = _format_filing_summary(filing)
            yield f"event: filing\ndata: {json.dumps(summary)}\n\n"

        # Stream risk if requested
        if include_risk or self._mentions_risk(query):
            risk = _calculate_risk(filings)
            yield f"event: risk\ndata: {json.dumps(risk)}\n\n"

        # Done event
        yield f"event: done\ndata: {json.dumps({'status': 'complete'})}\n\n"

    # --- Private helpers ---

    def _extract_debtor(self, query: str) -> str | None:
        """Extract a debtor name from the query using simple heuristics."""
        known = [
            "Acme Corporation",
            "Greenfield Logistics",
            "Lone Star Energy Solutions",
            "Pacific Ridge Technologies",
            "Midwest Agricultural Cooperative",
            "Sunshine Medical Group",
            "Harbor Shipping International",
        ]
        q_lower = query.lower()
        for name in known:
            if name.lower() in q_lower:
                return name
        # Fallback: look for "for <Name>" pattern
        if " for " in query:
            after_for = query.split(" for ", 1)[1]
            # Take words until we hit a preposition or end
            stop_words = {"in", "from", "at", "with", "on", "and", "or"}
            parts = []
            for word in after_for.split():
                cleaned = word.strip(".,;:!?")
                if cleaned.lower() in stop_words:
                    break
                parts.append(cleaned)
            if parts:
                return " ".join(parts)
        return None

    def _extract_state(self, query: str) -> str | None:
        """Extract a state name from the query."""
        states = {
            "new york": "New York",
            "california": "California",
            "texas": "Texas",
            "florida": "Florida",
            "illinois": "Illinois",
        }
        q_lower = query.lower()
        for key, value in states.items():
            if key in q_lower:
                return value
        return None

    def _mentions_risk(self, query: str) -> bool:
        """Check if the query mentions risk-related terms."""
        risk_words = {"risk", "exposure", "assess", "evaluate", "risky", "danger"}
        q_lower = query.lower()
        return any(w in q_lower for w in risk_words)

    def _build_answer(
        self, debtor_name: str | None, filings: list[dict], state: str | None
    ) -> str:
        """Build a natural-language answer from search results."""
        if not filings:
            target = debtor_name or "the specified entity"
            loc = f" in {state}" if state else ""
            return (
                f"No UCC filings were found for {target}{loc}. "
                f"This could mean the entity has no secured transactions on record, "
                f"or the name may be spelled differently in official filings."
            )

        debtor = filings[0]["debtor"]["name"]
        states = sorted(set(f["state"] for f in filings))
        count = len(filings)

        lines = [
            f"Found {count} UCC filing(s) for {debtor}"
            + (f" in {state}" if state else f" across {', '.join(states)}")
            + ".",
            "",
        ]

        for f in filings:
            lines.append(
                f"- **{f['filing_number']}** ({f['type']}, {f['status']}): "
                f"Filed {f['filing_date']} in {f['state']}. "
                f"Secured party: {f['secured_party']['name']}. "
                f"Collateral: {f['collateral_description'][:80]}..."
            )

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    agent = MockUCCAgent()

    print("=== Sync Query ===")
    result = agent.query("Find all UCC filings for Acme Corporation in New York")
    print(f"Answer: {result['answer'][:200]}...")
    print(f"Filings: {len(result['filings'])}")
    print(f"Time: {result['processing_time_ms']}ms")

    print("\n=== Streaming Query ===")
    for chunk in agent.query_stream("Find filings for Acme Corporation", include_risk=True):
        print(chunk.strip())
