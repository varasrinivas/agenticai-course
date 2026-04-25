"""
Mock data for UCC Entity Resolution Agent.
(Solution — identical to starter/mock_data.py)
"""

# ---------------------------------------------------------------------------
# UCC Filings Database
# ---------------------------------------------------------------------------
UCC_FILINGS = {
    "CA": {
        "CA-2023-0847291": {
            "filing_number": "CA-2023-0847291", "state": "CA", "filing_type": "UCC-1",
            "filing_date": "2023-03-15", "debtor_name": "Acme Corp",
            "debtor_address": "1200 Industrial Blvd, Suite 400, San Jose, CA 95112",
            "debtor_ein": "94-3829471", "secured_party": "Pacific Commerce Bank",
            "collateral_description": "All inventory, equipment, accounts receivable, and general intangibles",
            "status": "active", "expiration_date": "2028-03-15", "amendments": [],
        },
        "CA-2024-0112834": {
            "filing_number": "CA-2024-0112834", "state": "CA", "filing_type": "UCC-1",
            "filing_date": "2024-01-22", "debtor_name": "ACME CORPORATION",
            "debtor_address": "1200 Industrial Blvd, Suite 400, San Jose, CA 95112",
            "debtor_ein": "94-3829471", "secured_party": "Western Capital Lending LLC",
            "collateral_description": "Equipment and fixtures located at 1200 Industrial Blvd, San Jose, CA",
            "status": "active", "expiration_date": "2029-01-22", "amendments": [],
        },
        "CA-2022-0553192": {
            "filing_number": "CA-2022-0553192", "state": "CA", "filing_type": "UCC-1",
            "filing_date": "2022-08-10", "debtor_name": "Pinnacle Systems International",
            "debtor_address": "8900 Gateway Drive, Los Angeles, CA 90045",
            "debtor_ein": "95-7712034", "secured_party": "First National Business Credit",
            "collateral_description": "All assets including accounts, chattel paper, equipment, general intangibles, instruments, inventory",
            "status": "active", "expiration_date": "2027-08-10",
            "amendments": [{"amendment_number": "CA-2023-AMD-001", "date": "2023-06-01", "type": "collateral_change", "description": "Added intellectual property as collateral"}],
        },
        "CA-2021-0289451": {
            "filing_number": "CA-2021-0289451", "state": "CA", "filing_type": "UCC-1",
            "filing_date": "2021-05-20", "debtor_name": "Acme Corp dba AcmeTech Solutions",
            "debtor_address": "1200 Industrial Blvd, Suite 400, San Jose, CA 95112",
            "debtor_ein": "94-3829471", "secured_party": "Silicon Valley Equipment Finance",
            "collateral_description": "Specific equipment: CNC machinery serial numbers CMX-4400, CMX-4401, CMX-4402",
            "status": "active", "expiration_date": "2026-05-20", "amendments": [],
        },
        "CA-2023-0991204": {
            "filing_number": "CA-2023-0991204", "state": "CA", "filing_type": "UCC-1",
            "filing_date": "2023-11-05", "debtor_name": "Acme Holdings LLC",
            "debtor_address": "2500 Venture Parkway, Palo Alto, CA 94301",
            "debtor_ein": "94-5501287", "secured_party": "Bay Area Commercial Lending",
            "collateral_description": "Membership interests and equity in subsidiaries",
            "status": "active", "expiration_date": "2028-11-05", "amendments": [],
        },
    },
    "NV": {
        "NV-2023-0034521": {
            "filing_number": "NV-2023-0034521", "state": "NV", "filing_type": "UCC-1",
            "filing_date": "2023-06-12", "debtor_name": "Acme Corporation",
            "debtor_address": "100 Commerce Center Drive, Reno, NV 89501",
            "debtor_ein": "94-3829471", "secured_party": "Nevada Business Finance Corp",
            "collateral_description": "Inventory and equipment at Reno distribution facility",
            "status": "active", "expiration_date": "2028-06-12", "amendments": [],
        },
        "NV-2024-0008871": {
            "filing_number": "NV-2024-0008871", "state": "NV", "filing_type": "UCC-1",
            "filing_date": "2024-02-28", "debtor_name": "Pinnacle Systems Intl",
            "debtor_address": "4400 South Virginia Street, Reno, NV 89502",
            "debtor_ein": "95-7712034", "secured_party": "Mountain West Capital Partners",
            "collateral_description": "Accounts receivable and contract rights",
            "status": "active", "expiration_date": "2029-02-28", "amendments": [],
        },
    },
    "TX": {
        "TX-2022-1847592": {
            "filing_number": "TX-2022-1847592", "state": "TX", "filing_type": "UCC-1",
            "filing_date": "2022-11-03", "debtor_name": "Acme Corp",
            "debtor_address": "5600 Research Park Drive, Austin, TX 78759",
            "debtor_ein": "94-3829471", "secured_party": "Lone Star Business Credit",
            "collateral_description": "All inventory, accounts receivable, and equipment at Austin facility",
            "status": "active", "expiration_date": "2027-11-03",
            "amendments": [{"amendment_number": "TX-2023-AMD-001", "date": "2023-09-15", "type": "continuation", "description": "Five-year continuation statement filed"}],
        },
        "TX-2024-0229183": {
            "filing_number": "TX-2024-0229183", "state": "TX", "filing_type": "UCC-1",
            "filing_date": "2024-03-10", "debtor_name": "ACME CORP",
            "debtor_address": "5600 Research Park Drive, Austin, TX 78759",
            "debtor_ein": "94-3829471", "secured_party": "Texas Regional Bank",
            "collateral_description": "Line of credit secured by accounts receivable",
            "status": "active", "expiration_date": "2029-03-10", "amendments": [],
        },
        "TX-2023-1102847": {
            "filing_number": "TX-2023-1102847", "state": "TX", "filing_type": "UCC-1",
            "filing_date": "2023-04-22", "debtor_name": "Pinnacle Systems International Inc",
            "debtor_address": "7200 MoPac Expressway, Suite 300, Austin, TX 78731",
            "debtor_ein": "95-7712034", "secured_party": "Capital One Commercial Banking",
            "collateral_description": "All assets",
            "status": "active", "expiration_date": "2028-04-22", "amendments": [],
        },
    },
    "NY": {
        "NY-2023-0558291": {
            "filing_number": "NY-2023-0558291", "state": "NY", "filing_type": "UCC-1",
            "filing_date": "2023-07-18", "debtor_name": "Acme Corporation",
            "debtor_address": "350 Fifth Avenue, Suite 5100, New York, NY 10118",
            "debtor_ein": "94-3829471", "secured_party": "Manhattan Commercial Finance",
            "collateral_description": "Accounts receivable, contract rights, and general intangibles",
            "status": "active", "expiration_date": "2028-07-18", "amendments": [],
        },
        "NY-2022-0341829": {
            "filing_number": "NY-2022-0341829", "state": "NY", "filing_type": "UCC-1",
            "filing_date": "2022-12-05", "debtor_name": "Pinnacle Systems International",
            "debtor_address": "One Penn Plaza, Suite 2200, New York, NY 10119",
            "debtor_ein": "95-7712034", "secured_party": "JPMorgan Chase Commercial Banking",
            "collateral_description": "All inventory, equipment, accounts, chattel paper, instruments, and general intangibles",
            "status": "active", "expiration_date": "2027-12-05",
            "amendments": [{"amendment_number": "NY-2024-AMD-001", "date": "2024-01-15", "type": "secured_party_change", "description": "Assignment of security interest to Chase Capital Markets"}],
        },
    },
    "DE": {
        "DE-2021-0091447": {
            "filing_number": "DE-2021-0091447", "state": "DE", "filing_type": "UCC-1",
            "filing_date": "2021-09-30", "debtor_name": "Acme Corp",
            "debtor_address": "1209 Orange Street, Wilmington, DE 19801",
            "debtor_ein": "94-3829471", "secured_party": "Delaware Trust Financial",
            "collateral_description": "All assets now owned or hereafter acquired",
            "status": "active", "expiration_date": "2026-09-30",
            "amendments": [{"amendment_number": "DE-2023-AMD-001", "date": "2023-03-01", "type": "debtor_name_change", "description": "Debtor name updated from 'Acme Corp' to 'Acme Corporation' per entity name change filed with DE Secretary of State"}],
        },
        "DE-2023-0145592": {
            "filing_number": "DE-2023-0145592", "state": "DE", "filing_type": "UCC-1",
            "filing_date": "2023-05-14", "debtor_name": "Trident Logistics Group LLC",
            "debtor_address": "300 Delaware Avenue, Suite 900, Wilmington, DE 19801",
            "debtor_ein": "51-0482193", "secured_party": "Citizens Business Capital",
            "collateral_description": "Fleet vehicles, transportation equipment, and related assets",
            "status": "active", "expiration_date": "2028-05-14", "amendments": [],
        },
        "DE-2024-0023891": {
            "filing_number": "DE-2024-0023891", "state": "DE", "filing_type": "UCC-1",
            "filing_date": "2024-01-08", "debtor_name": "Trident Logistics Group (formerly Pinnacle Transport Services)",
            "debtor_address": "300 Delaware Avenue, Suite 900, Wilmington, DE 19801",
            "debtor_ein": "51-0482193", "secured_party": "Wells Fargo Equipment Finance",
            "collateral_description": "Specific equipment: Refrigerated trailers RFT-001 through RFT-050",
            "status": "active", "expiration_date": "2029-01-08", "amendments": [],
        },
    },
}

# ---------------------------------------------------------------------------
# Business Registry Data
# ---------------------------------------------------------------------------
BUSINESS_REGISTRY = {
    "94-3829471": {
        "ein": "94-3829471", "legal_name": "Acme Corporation",
        "dba_names": ["Acme Corp", "AcmeTech Solutions", "Acme Industrial"],
        "entity_type": "Corporation", "state_of_incorporation": "DE",
        "incorporation_date": "2005-03-22", "status": "active",
        "registered_agent": "Corporation Service Company, 251 Little Falls Drive, Wilmington, DE 19808",
        "officers": [
            {"name": "Robert Chen", "title": "CEO", "since": "2018-01-01"},
            {"name": "Sarah Martinez", "title": "CFO", "since": "2020-06-15"},
            {"name": "David Kim", "title": "COO", "since": "2019-09-01"},
        ],
        "addresses": {
            "headquarters": "1200 Industrial Blvd, Suite 400, San Jose, CA 95112",
            "registered": "1209 Orange Street, Wilmington, DE 19801",
            "branches": ["100 Commerce Center Drive, Reno, NV 89501", "5600 Research Park Drive, Austin, TX 78759", "350 Fifth Avenue, Suite 5100, New York, NY 10118"],
        },
        "annual_revenue_range": "$50M-$100M",
        "employee_count_range": "200-500",
        "naics_codes": ["333249", "423830"],
        "name_history": [
            {"name": "Acme Corp", "effective_date": "2005-03-22", "end_date": "2022-01-15"},
            {"name": "Acme Corporation", "effective_date": "2022-01-15", "end_date": None},
        ],
    },
    "95-7712034": {
        "ein": "95-7712034", "legal_name": "Pinnacle Systems International Inc",
        "dba_names": ["Pinnacle Systems", "PSI Technology", "Pinnacle Systems Intl"],
        "entity_type": "Corporation", "state_of_incorporation": "DE",
        "incorporation_date": "2010-08-11", "status": "active",
        "registered_agent": "National Registered Agents Inc, 160 Greentree Drive, Dover, DE 19904",
        "officers": [
            {"name": "Marcus Wong", "title": "CEO", "since": "2015-03-01"},
            {"name": "Elena Petrov", "title": "CTO", "since": "2016-11-01"},
        ],
        "addresses": {
            "headquarters": "8900 Gateway Drive, Los Angeles, CA 90045",
            "registered": "160 Greentree Drive, Dover, DE 19904",
            "branches": ["4400 South Virginia Street, Reno, NV 89502", "7200 MoPac Expressway, Suite 300, Austin, TX 78731", "One Penn Plaza, Suite 2200, New York, NY 10119"],
        },
        "annual_revenue_range": "$25M-$50M",
        "employee_count_range": "100-200",
        "naics_codes": ["541512", "334111"],
        "name_history": [
            {"name": "Pinnacle Systems International", "effective_date": "2010-08-11", "end_date": "2019-04-01"},
            {"name": "Pinnacle Systems International Inc", "effective_date": "2019-04-01", "end_date": None},
        ],
    },
    "94-5501287": {
        "ein": "94-5501287", "legal_name": "Acme Holdings LLC",
        "dba_names": [], "entity_type": "LLC", "state_of_incorporation": "DE",
        "incorporation_date": "2018-07-10", "status": "active",
        "registered_agent": "Corporation Service Company, 251 Little Falls Drive, Wilmington, DE 19808",
        "officers": [{"name": "Robert Chen", "title": "Managing Member", "since": "2018-07-10"}],
        "addresses": {"headquarters": "2500 Venture Parkway, Palo Alto, CA 94301", "registered": "1209 Orange Street, Wilmington, DE 19801"},
        "annual_revenue_range": "Not reported — holding company",
        "employee_count_range": "1-10",
        "naics_codes": ["551112"],
        "name_history": [],
        "notes": "Parent holding company of Acme Corporation (EIN 94-3829471). Same CEO (Robert Chen) and same registered agent.",
    },
    "51-0482193": {
        "ein": "51-0482193", "legal_name": "Trident Logistics Group LLC",
        "dba_names": ["Trident Freight", "Pinnacle Transport Services"],
        "entity_type": "LLC", "state_of_incorporation": "DE",
        "incorporation_date": "2017-02-14", "status": "active",
        "registered_agent": "Incorp Services Inc, 1201 Orange Street, Wilmington, DE 19801",
        "officers": [{"name": "James Callahan", "title": "Managing Member", "since": "2017-02-14"}],
        "addresses": {"headquarters": "300 Delaware Avenue, Suite 900, Wilmington, DE 19801"},
        "annual_revenue_range": "$10M-$25M",
        "employee_count_range": "50-100",
        "naics_codes": ["484110", "484121"],
        "name_history": [
            {"name": "Pinnacle Transport Services LLC", "effective_date": "2017-02-14", "end_date": "2022-09-01"},
            {"name": "Trident Logistics Group LLC", "effective_date": "2022-09-01", "end_date": None},
        ],
        "notes": "Formerly 'Pinnacle Transport Services' — NO relation to 'Pinnacle Systems International' (EIN 95-7712034) despite similar naming. Different ownership, different industry.",
    },
}
