"""
M18 — Evaluation Dataset for UCC Research Agent
=================================================
20 test cases across 4 categories, using the M15B mock data.
This file is COMPLETE — do not modify the test cases.

Categories:
  - filing_search (6 cases): Can the agent find the right filings?
  - entity_resolution (5 cases): Can the agent resolve entity names correctly?
  - risk_analysis (5 cases): Can the agent assess lien risk accurately?
  - edge_case (4 cases): Does the agent handle tricky inputs gracefully?

Each test case includes:
  - id: Unique identifier (e.g., FS-001)
  - category: One of the 4 categories above
  - query: The user question to send to the agent
  - expected: Dict with expected_filings, expected_entity, expected_risk_level, key_facts
  - difficulty: easy, medium, or hard
"""

EVAL_CASES = [
    # =========================================================================
    # FILING SEARCH (6 cases)
    # =========================================================================
    {
        "id": "FS-001",
        "category": "filing_search",
        "query": "Find all UCC filings for Acme Corporation in New York.",
        "expected": {
            "expected_filings": ["UCC-2024-NY-0012847", "UCC-2024-NY-0015921"],
            "expected_entity": "Acme Corporation",
            "expected_risk_level": None,
            "key_facts": [
                "Atlantic Capital Partners",
                "Citibank N.A.",
                "accounts receivable",
                "deposit accounts",
            ],
        },
        "difficulty": "easy",
    },
    {
        "id": "FS-002",
        "category": "filing_search",
        "query": "Show me all active filings in Texas.",
        "expected": {
            "expected_filings": [
                "UCC-2023-TX-0187634",
                "UCC-2024-TX-0201337",
                "UCC-2024-TX-0215890",
            ],
            "expected_entity": None,
            "expected_risk_level": None,
            "key_facts": [
                "Lone Star Energy Solutions",
                "Acme Corporation",
                "Caterpillar",
                "Wells Fargo",
            ],
        },
        "difficulty": "easy",
    },
    {
        "id": "FS-003",
        "category": "filing_search",
        "query": "What filings does Lone Star Energy Solutions have?",
        "expected": {
            "expected_filings": ["UCC-2023-TX-0187634", "UCC-2024-TX-0215890"],
            "expected_entity": "Lone Star Energy Solutions LP",
            "expected_risk_level": None,
            "key_facts": [
                "hydraulic excavators",
                "Caterpillar",
                "Wells Fargo Equipment Finance",
                "track-type tractors",
            ],
        },
        "difficulty": "easy",
    },
    {
        "id": "FS-004",
        "category": "filing_search",
        "query": "Find filings for Acme Corporation across all states and list the secured parties.",
        "expected": {
            "expected_filings": [
                "UCC-2024-NY-0012847",
                "UCC-2024-NY-0015921",
                "UCC-2024-CA-0101457",
                "UCC-2024-TX-0201337",
                "UCC-2024-FL-0059811",
                "UCC-2024-IL-0081290",
            ],
            "expected_entity": "Acme Corporation",
            "expected_risk_level": None,
            "key_facts": [
                "Atlantic Capital Partners",
                "Citibank N.A.",
                "Bank of America",
                "PNC Bank",
                "JPMorgan Chase",
                "5 states",
            ],
        },
        "difficulty": "medium",
    },
    {
        "id": "FS-005",
        "category": "filing_search",
        "query": "Are there any terminated UCC filings in the database?",
        "expected": {
            "expected_filings": ["UCC-2023-NY-0145678"],
            "expected_entity": "Harbor Shipping International Inc",
            "expected_risk_level": None,
            "key_facts": [
                "Terminated",
                "Harbor Shipping",
                "Citibank",
                "UCC-2019-NY-0089012",
            ],
        },
        "difficulty": "medium",
    },
    {
        "id": "FS-006",
        "category": "filing_search",
        "query": "List all UCC-3 amendment filings and what they amended.",
        "expected": {
            "expected_filings": [
                "UCC-2023-CA-0087652",
                "UCC-2024-FL-0054219",
                "UCC-2023-IL-0069221",
            ],
            "expected_entity": None,
            "expected_risk_level": None,
            "key_facts": [
                "Pacific Ridge Technologies",
                "Sunshine Medical Group",
                "Midwest Agricultural Cooperative",
                "Amendment",
                "software source code",
                "MRI systems",
                "grain storage",
            ],
        },
        "difficulty": "medium",
    },

    # =========================================================================
    # ENTITY RESOLUTION (5 cases)
    # =========================================================================
    {
        "id": "ER-001",
        "category": "entity_resolution",
        "query": "Find filings for Acme Corp.",
        "expected": {
            "expected_filings": [
                "UCC-2024-NY-0012847",
                "UCC-2024-NY-0015921",
                "UCC-2024-CA-0101457",
                "UCC-2024-TX-0201337",
                "UCC-2024-FL-0059811",
                "UCC-2024-IL-0081290",
            ],
            "expected_entity": "Acme Corporation",
            "expected_risk_level": None,
            "key_facts": ["Acme Corporation", "6 filings"],
        },
        "difficulty": "easy",
    },
    {
        "id": "ER-002",
        "category": "entity_resolution",
        "query": "What liens does Pacific Ridge Tech have?",
        "expected": {
            "expected_filings": ["UCC-2024-CA-0098231", "UCC-2023-CA-0087652"],
            "expected_entity": "Pacific Ridge Technologies Inc",
            "expected_risk_level": None,
            "key_facts": [
                "Silicon Valley Bank",
                "intellectual property",
                "software source code",
            ],
        },
        "difficulty": "medium",
    },
    {
        "id": "ER-003",
        "category": "entity_resolution",
        "query": "Search for Lonestar Energy filings.",
        "expected": {
            "expected_filings": ["UCC-2023-TX-0187634", "UCC-2024-TX-0215890"],
            "expected_entity": "Lone Star Energy Solutions LP",
            "expected_risk_level": None,
            "key_facts": [
                "Lone Star Energy Solutions",
                "Texas",
                "equipment",
            ],
        },
        "difficulty": "medium",
    },
    {
        "id": "ER-004",
        "category": "entity_resolution",
        "query": "Does Greenfield Logistics have any UCC filings?",
        "expected": {
            "expected_filings": ["UCC-2024-NY-0019004"],
            "expected_entity": "Greenfield Logistics LLC",
            "expected_risk_level": None,
            "key_facts": [
                "JPMorgan Chase",
                "inventory",
                "warehouse facilities",
            ],
        },
        "difficulty": "easy",
    },
    {
        "id": "ER-005",
        "category": "entity_resolution",
        "query": "Find filings for the Midwest Ag Co-op in Illinois.",
        "expected": {
            "expected_filings": ["UCC-2024-IL-0076543", "UCC-2023-IL-0069221"],
            "expected_entity": "Midwest Agricultural Cooperative",
            "expected_risk_level": None,
            "key_facts": [
                "Farm Credit Services",
                "farm products",
                "grain storage",
                "John Deere",
            ],
        },
        "difficulty": "hard",
    },

    # =========================================================================
    # RISK ANALYSIS (5 cases)
    # =========================================================================
    {
        "id": "RA-001",
        "category": "risk_analysis",
        "query": "What is the lien risk level for Acme Corporation?",
        "expected": {
            "expected_filings": [
                "UCC-2024-NY-0012847",
                "UCC-2024-NY-0015921",
                "UCC-2024-CA-0101457",
                "UCC-2024-TX-0201337",
                "UCC-2024-FL-0059811",
                "UCC-2024-IL-0081290",
            ],
            "expected_entity": "Acme Corporation",
            "expected_risk_level": "HIGH",
            "key_facts": [
                "6 active filings",
                "5 states",
                "multiple secured parties",
                "blanket lien",
            ],
        },
        "difficulty": "medium",
    },
    {
        "id": "RA-002",
        "category": "risk_analysis",
        "query": "Assess the risk for Lone Star Energy Solutions.",
        "expected": {
            "expected_filings": ["UCC-2023-TX-0187634", "UCC-2024-TX-0215890"],
            "expected_entity": "Lone Star Energy Solutions LP",
            "expected_risk_level": "MEDIUM",
            "key_facts": [
                "2 filings",
                "equipment-specific",
                "Texas only",
                "no blanket liens",
            ],
        },
        "difficulty": "medium",
    },
    {
        "id": "RA-003",
        "category": "risk_analysis",
        "query": "How risky is Pacific Ridge Technologies from a lien perspective?",
        "expected": {
            "expected_filings": ["UCC-2024-CA-0098231", "UCC-2023-CA-0087652"],
            "expected_entity": "Pacific Ridge Technologies Inc",
            "expected_risk_level": "HIGH",
            "key_facts": [
                "all assets",
                "intellectual property",
                "blanket lien",
                "Silicon Valley Bank",
            ],
        },
        "difficulty": "medium",
    },
    {
        "id": "RA-004",
        "category": "risk_analysis",
        "query": "What's the risk profile for Greenfield Logistics?",
        "expected": {
            "expected_filings": ["UCC-2024-NY-0019004"],
            "expected_entity": "Greenfield Logistics LLC",
            "expected_risk_level": "LOW",
            "key_facts": [
                "1 filing",
                "single state",
                "inventory and receivables",
            ],
        },
        "difficulty": "easy",
    },
    {
        "id": "RA-005",
        "category": "risk_analysis",
        "query": "Compare the lien risk between Acme Corporation and Greenfield Logistics.",
        "expected": {
            "expected_filings": [
                "UCC-2024-NY-0012847",
                "UCC-2024-NY-0015921",
                "UCC-2024-CA-0101457",
                "UCC-2024-TX-0201337",
                "UCC-2024-FL-0059811",
                "UCC-2024-IL-0081290",
                "UCC-2024-NY-0019004",
            ],
            "expected_entity": "Acme Corporation",
            "expected_risk_level": "HIGH",
            "key_facts": [
                "Acme",
                "HIGH",
                "Greenfield",
                "LOW",
                "6 filings vs 1 filing",
            ],
        },
        "difficulty": "hard",
    },

    # =========================================================================
    # EDGE CASES (4 cases)
    # =========================================================================
    {
        "id": "EC-001",
        "category": "edge_case",
        "query": "Find all filings for XYZ Nonexistent Industries.",
        "expected": {
            "expected_filings": [],
            "expected_entity": "XYZ Nonexistent Industries",
            "expected_risk_level": None,
            "key_facts": [
                "no filings found",
                "no results",
            ],
        },
        "difficulty": "easy",
    },
    {
        "id": "EC-002",
        "category": "edge_case",
        "query": "Find filings for A.C.M.E. Corporation in New York and California.",
        "expected": {
            "expected_filings": [
                "UCC-2024-NY-0012847",
                "UCC-2024-NY-0015921",
                "UCC-2024-CA-0101457",
            ],
            "expected_entity": "Acme Corporation",
            "expected_risk_level": None,
            "key_facts": [
                "Acme Corporation",
                "New York",
                "California",
            ],
        },
        "difficulty": "hard",
    },
    {
        "id": "EC-003",
        "category": "edge_case",
        "query": "Show me filings in Alaska and Hawaii.",
        "expected": {
            "expected_filings": [],
            "expected_entity": None,
            "expected_risk_level": None,
            "key_facts": [
                "no filings found",
                "no results",
            ],
        },
        "difficulty": "medium",
    },
    {
        "id": "EC-004",
        "category": "edge_case",
        "query": "Which debtors have filings that are about to expire in the next year?",
        "expected": {
            "expected_filings": [],
            "expected_entity": None,
            "expected_risk_level": None,
            "key_facts": [
                "no filings expiring",
                "earliest expiration",
            ],
        },
        "difficulty": "hard",
    },
]


# --- Mock agent responses for testing without an actual agent ---
# These simulate what a well-functioning agent WOULD return for each query.
MOCK_AGENT_RESPONSES = {
    "FS-001": (
        "I found 2 UCC filings for Acme Corporation in New York:\n\n"
        "1. **UCC-2024-NY-0012847** (UCC-1, Active)\n"
        "   - Secured Party: Atlantic Capital Partners\n"
        "   - Collateral: All accounts receivable, inventory, equipment, and general intangibles\n"
        "   - Filed: 2024-03-15, Expires: 2029-03-15\n\n"
        "2. **UCC-2024-NY-0015921** (UCC-1, Active)\n"
        "   - Secured Party: Citibank N.A.\n"
        "   - Collateral: All deposit accounts, investment property, and letter-of-credit rights\n"
        "   - Filed: 2024-05-22, Expires: 2029-05-22"
    ),
    "FS-002": (
        "I found 3 active filings in Texas:\n\n"
        "1. **UCC-2023-TX-0187634** — Lone Star Energy Solutions LP\n"
        "   - Secured Party: Wells Fargo Equipment Finance\n"
        "   - Collateral: Caterpillar excavators and Liebherr crane\n\n"
        "2. **UCC-2024-TX-0201337** — Acme Corporation\n"
        "   - Secured Party: PNC Bank N.A.\n"
        "   - Collateral: Accounts receivable and contract rights\n\n"
        "3. **UCC-2024-TX-0215890** — Lone Star Energy Solutions LP\n"
        "   - Secured Party: Caterpillar Financial Services Corp\n"
        "   - Collateral: Caterpillar D10T2 track-type tractors"
    ),
    "FS-003": (
        "Lone Star Energy Solutions LP has 2 UCC filings, both in Texas:\n\n"
        "1. **UCC-2023-TX-0187634** (UCC-1, Active)\n"
        "   - Secured Party: Wells Fargo Equipment Finance\n"
        "   - Collateral: 3 Caterpillar 349F L hydraulic excavators and 1 Liebherr mobile crane\n\n"
        "2. **UCC-2024-TX-0215890** (UCC-1, Active)\n"
        "   - Secured Party: Caterpillar Financial Services Corp\n"
        "   - Collateral: 2 Caterpillar D10T2 track-type tractors"
    ),
    "FS-004": (
        "Acme Corporation has 6 filings across 5 states:\n\n"
        "- **UCC-2024-NY-0012847** (NY) — Atlantic Capital Partners\n"
        "- **UCC-2024-NY-0015921** (NY) — Citibank N.A.\n"
        "- **UCC-2024-CA-0101457** (CA) — Bank of America N.A.\n"
        "- **UCC-2024-TX-0201337** (TX) — PNC Bank N.A.\n"
        "- **UCC-2024-FL-0059811** (FL) — Atlantic Capital Partners\n"
        "- **UCC-2024-IL-0081290** (IL) — JPMorgan Chase Bank N.A.\n\n"
        "The company has liens with 5 different secured parties across 5 states."
    ),
    "FS-005": (
        "Yes, there is 1 terminated UCC filing:\n\n"
        "**UCC-2023-NY-0145678** (UCC-3, Terminated)\n"
        "- Debtor: Harbor Shipping International Inc\n"
        "- Secured Party: Citibank N.A.\n"
        "- This filing terminates original filing UCC-2019-NY-0089012."
    ),
    "FS-006": (
        "There are 3 UCC-3 amendment filings:\n\n"
        "1. **UCC-2023-CA-0087652** — Pacific Ridge Technologies Inc\n"
        "   - Amends: UCC-2024-CA-0098231\n"
        "   - Added: software source code repositories, SaaS subscription contracts\n\n"
        "2. **UCC-2024-FL-0054219** — Sunshine Medical Group PA\n"
        "   - Amends: UCC-2022-FL-0031456\n"
        "   - Added: Siemens MRI systems and GE CT scanner\n\n"
        "3. **UCC-2023-IL-0069221** — Midwest Agricultural Cooperative\n"
        "   - Amends: UCC-2024-IL-0076543\n"
        "   - Added: grain storage facility equipment and John Deere combines"
    ),
    "ER-001": (
        "I found 6 filings for Acme Corporation across all states:\n\n"
        "- UCC-2024-NY-0012847 (New York)\n"
        "- UCC-2024-NY-0015921 (New York)\n"
        "- UCC-2024-CA-0101457 (California)\n"
        "- UCC-2024-TX-0201337 (Texas)\n"
        "- UCC-2024-FL-0059811 (Florida)\n"
        "- UCC-2024-IL-0081290 (Illinois)\n\n"
        "Note: You searched for 'Acme Corp' — the full legal name is 'Acme Corporation'."
    ),
    "ER-002": (
        "Pacific Ridge Technologies Inc has 2 filings in California:\n\n"
        "1. **UCC-2024-CA-0098231** (UCC-1, Active)\n"
        "   - Secured Party: Silicon Valley Bank\n"
        "   - Collateral: All assets including intellectual property, patents, trademarks\n\n"
        "2. **UCC-2023-CA-0087652** (UCC-3, Amendment)\n"
        "   - Secured Party: Silicon Valley Bank\n"
        "   - Added: software source code repositories, SaaS contracts"
    ),
    "ER-003": (
        "I found 2 filings for Lone Star Energy Solutions LP in Texas:\n\n"
        "1. **UCC-2023-TX-0187634** — equipment filing with Wells Fargo\n"
        "2. **UCC-2024-TX-0215890** — equipment filing with Caterpillar Financial\n\n"
        "Note: You searched for 'Lonestar Energy' — the legal name is "
        "'Lone Star Energy Solutions LP' (two words: Lone Star)."
    ),
    "ER-004": (
        "Greenfield Logistics LLC has 1 UCC filing:\n\n"
        "**UCC-2024-NY-0019004** (UCC-1, Active)\n"
        "- Secured Party: JPMorgan Chase Bank N.A.\n"
        "- Collateral: All inventory at warehouse facilities in New York State; "
        "all accounts receivable from distribution operations\n"
        "- Filed: 2024-08-10, Expires: 2029-08-10"
    ),
    "ER-005": (
        "Midwest Agricultural Cooperative has 2 filings in Illinois:\n\n"
        "1. **UCC-2024-IL-0076543** (UCC-1, Active)\n"
        "   - Secured Party: Farm Credit Services of America\n"
        "   - Collateral: All farm products (corn, soybeans, wheat), livestock, farm equipment\n\n"
        "2. **UCC-2023-IL-0069221** (UCC-3, Amendment)\n"
        "   - Secured Party: Farm Credit Services of America\n"
        "   - Added: grain storage facility equipment, 4 John Deere S790 combines"
    ),
    "RA-001": (
        "**Risk Assessment: Acme Corporation — HIGH RISK**\n\n"
        "Filings analyzed: UCC-2024-NY-0012847, UCC-2024-NY-0015921, "
        "UCC-2024-CA-0101457, UCC-2024-TX-0201337, UCC-2024-FL-0059811, "
        "UCC-2024-IL-0081290\n\n"
        "- Total Active Filings: 6 active filings across 5 states (NY, CA, TX, FL, IL)\n"
        "- Multiple Secured Parties: Atlantic Capital Partners, Citibank N.A., "
        "Bank of America, PNC Bank, JPMorgan Chase\n"
        "- Collateral Concern: Includes blanket lien on 'all assets' language "
        "in several filings (accounts receivable, inventory, equipment, general intangibles)\n"
        "- Risk Factors: Multi-state exposure, overlapping collateral descriptions, "
        "high number of active liens\n\n"
        "Recommendation: Conduct thorough due diligence before extending credit."
    ),
    "RA-002": (
        "**Risk Assessment: Lone Star Energy Solutions LP — MEDIUM RISK**\n\n"
        "Filings analyzed: UCC-2023-TX-0187634, UCC-2024-TX-0215890\n\n"
        "- Total Active Filings: 2 filings in Texas only\n"
        "- Secured Parties: Wells Fargo Equipment Finance, Caterpillar Financial\n"
        "- Collateral: Equipment-specific liens (excavators, cranes, tractors) — "
        "no blanket liens on general assets\n"
        "- Risk Factors: Multiple equipment financings suggest capital-intensive "
        "operations but liens are narrow and specific\n\n"
        "Recommendation: Moderate risk — equipment liens are standard for this industry."
    ),
    "RA-003": (
        "**Risk Assessment: Pacific Ridge Technologies Inc — HIGH RISK**\n\n"
        "Filings analyzed: UCC-2024-CA-0098231, UCC-2023-CA-0087652\n\n"
        "- Total Filings: 2 in California (1 original + 1 amendment)\n"
        "- Secured Party: Silicon Valley Bank\n"
        "- Collateral Concern: Blanket lien on all assets including intellectual property, "
        "patents, trademarks, plus amendment adding software source code and SaaS contracts\n"
        "- Risk Factors: Single lender has a claim on virtually every asset class\n\n"
        "Recommendation: High risk due to comprehensive blanket lien by Silicon Valley Bank."
    ),
    "RA-004": (
        "**Risk Assessment: Greenfield Logistics LLC — LOW RISK**\n\n"
        "Filing analyzed: UCC-2024-NY-0019004\n\n"
        "- Total Active Filings: 1 filing in New York (single state)\n"
        "- Secured Party: JPMorgan Chase Bank N.A.\n"
        "- Collateral: Inventory at warehouse facilities and accounts receivable — "
        "standard operating line of credit (inventory and receivables)\n"
        "- Risk Factors: Single filing, single state, collateral limited to "
        "inventory and receivables\n\n"
        "Recommendation: Low risk — this is a standard commercial lending arrangement."
    ),
    "RA-005": (
        "**Comparative Risk Analysis: Acme Corporation vs Greenfield Logistics**\n\n"
        "**Acme Corporation — HIGH RISK**\n"
        "Filings: UCC-2024-NY-0012847, UCC-2024-NY-0015921, UCC-2024-CA-0101457, "
        "UCC-2024-TX-0201337, UCC-2024-FL-0059811, UCC-2024-IL-0081290\n"
        "- 6 active filings across 5 states\n"
        "- 5 different secured parties\n"
        "- Blanket liens on substantially all assets\n\n"
        "**Greenfield Logistics LLC — LOW RISK**\n"
        "Filing: UCC-2024-NY-0019004\n"
        "- 1 filing in New York\n"
        "- Single secured party (JPMorgan Chase)\n"
        "- Limited collateral scope\n\n"
        "Acme has 6 filings vs 1 filing for Greenfield, with significantly "
        "broader collateral exposure and multi-state complexity."
    ),
    "EC-001": (
        "I searched for 'XYZ Nonexistent Industries' but found no filings matching "
        "that entity name. No results were returned from any state.\n\n"
        "Suggestions:\n"
        "- Verify the exact legal name of the entity\n"
        "- Try alternative name variations or abbreviations\n"
        "- The entity may not have any UCC filings on record"
    ),
    "EC-002": (
        "I interpreted 'A.C.M.E. Corporation' as 'Acme Corporation' and found "
        "3 filings in New York and California:\n\n"
        "- **UCC-2024-NY-0012847** — Acme Corporation, New York\n"
        "- **UCC-2024-NY-0015921** — Acme Corporation, New York\n"
        "- **UCC-2024-CA-0101457** — Acme Corporation, California"
    ),
    "EC-003": (
        "I searched for filings in Alaska and Hawaii but found no results. "
        "The database currently contains filings for the following states: "
        "California, Florida, Illinois, New York, and Texas."
    ),
    "EC-004": (
        "Looking at all active filings, none have expiration dates within the "
        "next year (no filings expiring soon). The earliest expiration is for "
        "Sunshine Medical Group PA which expires on 2027-11-18. All other "
        "filings expire between 2028 and 2029."
    ),
}


def get_cases_by_category(category: str) -> list[dict]:
    """Return all test cases for a given category."""
    return [c for c in EVAL_CASES if c["category"] == category]


def get_case_by_id(case_id: str) -> dict | None:
    """Look up a single test case by ID."""
    for case in EVAL_CASES:
        if case["id"] == case_id:
            return case
    return None


def get_mock_response(case_id: str) -> str:
    """Return the mock agent response for a given test case ID."""
    return MOCK_AGENT_RESPONSES.get(case_id, "No mock response available.")


def get_summary() -> dict:
    """Return summary statistics about the eval dataset."""
    categories = {}
    difficulties = {}
    for case in EVAL_CASES:
        cat = case["category"]
        diff = case["difficulty"]
        categories[cat] = categories.get(cat, 0) + 1
        difficulties[diff] = difficulties.get(diff, 0) + 1
    return {
        "total_cases": len(EVAL_CASES),
        "categories": categories,
        "difficulties": difficulties,
    }


if __name__ == "__main__":
    summary = get_summary()
    print(f"M18 Eval Dataset: {summary['total_cases']} test cases")
    print(f"\nBy category:")
    for cat, count in sorted(summary["categories"].items()):
        print(f"  {cat}: {count}")
    print(f"\nBy difficulty:")
    for diff, count in sorted(summary["difficulties"].items()):
        print(f"  {diff}: {count}")
    print(f"\nTest case IDs:")
    for case in EVAL_CASES:
        print(f"  [{case['id']}] ({case['difficulty']:6s}) {case['query'][:60]}...")
