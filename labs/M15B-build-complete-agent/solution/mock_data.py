"""
M15B — Mock UCC Filing Data (Complete — do not modify)
=======================================================
15 realistic UCC filings across NY, CA, TX, FL, IL — plus
helper functions for searching and retrieval.

This file is COMPLETE because students build agent logic,
not data infrastructure. The filings are realistic enough to
demonstrate search, risk analysis, and multi-agent coordination.
"""


MOCK_FILINGS = [
    # --- NEW YORK (4 filings) ---
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
            "jurisdiction": "New York"
        },
        "secured_party": {
            "name": "Atlantic Capital Partners",
            "address": "1 Chase Manhattan Plaza, Floor 45, New York, NY 10005"
        },
        "collateral_description": "All accounts receivable, inventory, equipment, and general intangibles now owned or hereafter acquired by Debtor.",
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
            "jurisdiction": "New York"
        },
        "secured_party": {
            "name": "Citibank N.A.",
            "address": "388 Greenwich Street, New York, NY 10013"
        },
        "collateral_description": "All deposit accounts, investment property, and letter-of-credit rights held at or through Citibank.",
    },
    {
        "filing_number": "UCC-2023-NY-0145678",
        "type": "UCC-3",
        "state": "New York",
        "filing_date": "2023-12-01",
        "expiration_date": None,
        "status": "Terminated",
        "debtor": {
            "name": "Harbor Shipping International Inc",
            "address": "One World Trade Center, Floor 72, New York, NY 10007",
            "org_type": "Corporation",
            "jurisdiction": "New York"
        },
        "secured_party": {
            "name": "Citibank N.A.",
            "address": "388 Greenwich Street, New York, NY 10013"
        },
        "collateral_description": "TERMINATION — This filing terminates the effectiveness of the original filing UCC-2019-NY-0089012.",
        "original_filing": "UCC-2019-NY-0089012"
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
            "jurisdiction": "New York"
        },
        "secured_party": {
            "name": "JPMorgan Chase Bank N.A.",
            "address": "383 Madison Avenue, New York, NY 10179"
        },
        "collateral_description": "All inventory held at debtor's warehouse facilities in New York State; all accounts receivable arising from distribution operations.",
    },

    # --- CALIFORNIA (3 filings) ---
    {
        "filing_number": "UCC-2024-CA-0098231",
        "type": "UCC-1",
        "state": "California",
        "filing_date": "2024-01-22",
        "expiration_date": "2029-01-22",
        "status": "Active",
        "debtor": {
            "name": "Pacific Ridge Technologies Inc",
            "address": "2800 Sand Hill Road, Menlo Park, CA 94025",
            "org_type": "Corporation",
            "jurisdiction": "Delaware"
        },
        "secured_party": {
            "name": "Silicon Valley Bank",
            "address": "3003 Tasman Drive, Santa Clara, CA 95054"
        },
        "collateral_description": "All assets of the Debtor including but not limited to: intellectual property, patents, trademarks, accounts, deposit accounts, investment property, and all proceeds thereof.",
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
            "jurisdiction": "New York"
        },
        "secured_party": {
            "name": "Bank of America N.A.",
            "address": "555 California Street, San Francisco, CA 94104"
        },
        "collateral_description": "All equipment and fixtures located at debtor's San Francisco and Los Angeles offices.",
    },
    {
        "filing_number": "UCC-2023-CA-0087652",
        "type": "UCC-3",
        "state": "California",
        "filing_date": "2023-11-15",
        "expiration_date": "2028-06-30",
        "status": "Amendment",
        "debtor": {
            "name": "Pacific Ridge Technologies Inc",
            "address": "2800 Sand Hill Road, Menlo Park, CA 94025",
            "org_type": "Corporation",
            "jurisdiction": "Delaware"
        },
        "secured_party": {
            "name": "Silicon Valley Bank",
            "address": "3003 Tasman Drive, Santa Clara, CA 95054"
        },
        "collateral_description": "Amendment to add: all software source code repositories, SaaS subscription contracts, and recurring revenue streams. Original collateral description unchanged.",
        "original_filing": "UCC-2024-CA-0098231"
    },

    # --- TEXAS (3 filings) ---
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
            "jurisdiction": "Texas"
        },
        "secured_party": {
            "name": "Wells Fargo Equipment Finance",
            "address": "301 South College Street, Charlotte, NC 28202"
        },
        "collateral_description": "Specific equipment: (3) Caterpillar 349F L hydraulic excavators, serial numbers CAT349F-8821, CAT349F-8822, CAT349F-8823; (1) Liebherr LTM 1300-6.2 mobile crane, serial number LTM-DE-90124.",
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
            "jurisdiction": "New York"
        },
        "secured_party": {
            "name": "PNC Bank N.A.",
            "address": "300 Fifth Avenue, Pittsburgh, PA 15222"
        },
        "collateral_description": "All accounts receivable and contract rights arising from debtor's Texas operations.",
    },
    {
        "filing_number": "UCC-2024-TX-0215890",
        "type": "UCC-1",
        "state": "Texas",
        "filing_date": "2024-06-15",
        "expiration_date": "2029-06-15",
        "status": "Active",
        "debtor": {
            "name": "Lone Star Energy Solutions LP",
            "address": "1200 Smith Street, Suite 3000, Houston, TX 77002",
            "org_type": "Limited Partnership",
            "jurisdiction": "Texas"
        },
        "secured_party": {
            "name": "Caterpillar Financial Services Corp",
            "address": "2120 West End Avenue, Nashville, TN 37203"
        },
        "collateral_description": "Specific equipment: (2) Caterpillar D10T2 track-type tractors, serial numbers CAT-D10T2-4401 and CAT-D10T2-4402.",
    },

    # --- FLORIDA (2 filings) ---
    {
        "filing_number": "UCC-2024-FL-0054219",
        "type": "UCC-3",
        "state": "Florida",
        "filing_date": "2024-06-01",
        "expiration_date": "2027-11-18",
        "status": "Amendment",
        "debtor": {
            "name": "Sunshine Medical Group PA",
            "address": "4500 Biscayne Boulevard, Miami, FL 33137",
            "org_type": "Professional Association",
            "jurisdiction": "Florida"
        },
        "secured_party": {
            "name": "TD Bank N.A.",
            "address": "1701 Route 70 East, Cherry Hill, NJ 08034"
        },
        "collateral_description": "Amendment to add: (2) Siemens MAGNETOM Vida 3T MRI systems and (1) GE Revolution CT scanner. Original collateral description unchanged.",
        "original_filing": "UCC-2022-FL-0031456"
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
            "jurisdiction": "New York"
        },
        "secured_party": {
            "name": "Atlantic Capital Partners",
            "address": "1 Chase Manhattan Plaza, Floor 45, New York, NY 10005"
        },
        "collateral_description": "All accounts receivable, inventory, and general intangibles of debtor's Florida division.",
    },

    # --- ILLINOIS (3 filings) ---
    {
        "filing_number": "UCC-2024-IL-0076543",
        "type": "UCC-1",
        "state": "Illinois",
        "filing_date": "2024-02-14",
        "expiration_date": "2029-02-14",
        "status": "Active",
        "debtor": {
            "name": "Midwest Agricultural Cooperative",
            "address": "200 W Adams St, Suite 1500, Chicago, IL 60606",
            "org_type": "Cooperative",
            "jurisdiction": "Illinois"
        },
        "secured_party": {
            "name": "Farm Credit Services of America",
            "address": "5015 S 118th St, Omaha, NE 68137"
        },
        "collateral_description": "All farm products, including but not limited to crops (corn, soybeans, wheat), livestock, and farm equipment. All accounts and proceeds arising from the sale of farm products.",
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
            "jurisdiction": "New York"
        },
        "secured_party": {
            "name": "JPMorgan Chase Bank N.A.",
            "address": "383 Madison Avenue, New York, NY 10179"
        },
        "collateral_description": "All assets of debtor's Illinois subsidiary including accounts, inventory, equipment, and all proceeds thereof.",
    },
    {
        "filing_number": "UCC-2023-IL-0069221",
        "type": "UCC-3",
        "state": "Illinois",
        "filing_date": "2023-10-05",
        "expiration_date": "2028-02-14",
        "status": "Amendment",
        "debtor": {
            "name": "Midwest Agricultural Cooperative",
            "address": "200 W Adams St, Suite 1500, Chicago, IL 60606",
            "org_type": "Cooperative",
            "jurisdiction": "Illinois"
        },
        "secured_party": {
            "name": "Farm Credit Services of America",
            "address": "5015 S 118th St, Omaha, NE 68137"
        },
        "collateral_description": "Amendment to add: all grain storage facility equipment at Decatur, IL warehouse; (4) John Deere S790 combines, serial numbers JD-S790-2201 through JD-S790-2204.",
        "original_filing": "UCC-2024-IL-0076543"
    },
]


def search_filings(debtor_name: str = None, state: str = None,
                    status: str = None, filing_type: str = None) -> list[dict]:
    """Search filings by any combination of criteria. Case-insensitive partial match on names."""
    results = MOCK_FILINGS
    if debtor_name:
        results = [f for f in results if debtor_name.lower() in f["debtor"]["name"].lower()]
    if state:
        results = [f for f in results if f["state"].lower() == state.lower()]
    if status:
        results = [f for f in results if f["status"].lower() == status.lower()]
    if filing_type:
        results = [f for f in results if f["type"].lower() == filing_type.lower()]
    return results


def get_filing_by_number(filing_number: str) -> dict | None:
    """Look up a single filing by its filing number. Returns None if not found."""
    for filing in MOCK_FILINGS:
        if filing["filing_number"] == filing_number:
            return filing
    return None


def get_debtor_names() -> list[str]:
    """Return sorted list of unique debtor names."""
    return sorted(set(f["debtor"]["name"] for f in MOCK_FILINGS))


def get_states() -> list[str]:
    """Return sorted list of states with filings."""
    return sorted(set(f["state"] for f in MOCK_FILINGS))


def get_stats() -> dict:
    """Return summary statistics about the dataset."""
    return {
        "total_filings": len(MOCK_FILINGS),
        "active": len([f for f in MOCK_FILINGS if f["status"] == "Active"]),
        "terminated": len([f for f in MOCK_FILINGS if f["status"] == "Terminated"]),
        "amendments": len([f for f in MOCK_FILINGS if f["type"] == "UCC-3"]),
        "states": get_states(),
        "debtors": get_debtor_names(),
    }


if __name__ == "__main__":
    stats = get_stats()
    print(f"M15B Mock Data: {stats['total_filings']} filings across {len(stats['states'])} states")
    print(f"  Active: {stats['active']} | Terminated: {stats['terminated']} | Amendments: {stats['amendments']}")
    print(f"  States: {', '.join(stats['states'])}")
    print(f"  Debtors: {', '.join(stats['debtors'])}")
