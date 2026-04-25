"""
Mock data for UCC Data Engineering Pipeline — Multi-Agent Capstone.

Contains realistic UCC filing records in multiple formats (CSV, JSON, XML-like),
entity records with variations, collateral types, and quality rules.
16 filing batches with edge cases.
"""

# ---------------------------------------------------------------------------
# UCC Filing Batches (16 records, mixed formats, with edge cases)
# ---------------------------------------------------------------------------
FILING_BATCHES = {
    "BATCH-001": {
        "batch_id": "BATCH-001",
        "source": "secretary_of_state_CA",
        "format": "csv",
        "filing_count": 5,
        "filings": [
            {"filing_number": "UCC-2024-CA-00101", "debtor_name": "ACME CORP", "secured_party": "First National Bank", "collateral": "All inventory and equipment", "filing_date": "2024-01-15", "status": "active", "debtor_address": "123 Main St, Los Angeles, CA 90001", "debtor_ein": "12-3456789"},
            {"filing_number": "UCC-2024-CA-00102", "debtor_name": "Acme Corporation", "secured_party": "First National Bank", "collateral": "Accounts receivable", "filing_date": "2024-02-20", "status": "active", "debtor_address": "123 Main Street, Los Angeles, CA 90001", "debtor_ein": "12-3456789"},
            {"filing_number": "UCC-2024-CA-00103", "debtor_name": "PACIFIC COAST BUILDERS INC", "secured_party": "Western Credit Union", "collateral": "Construction equipment, vehicles", "filing_date": "2024-03-10", "status": "active", "debtor_address": "456 Oak Ave, San Francisco, CA 94102", "debtor_ein": "98-7654321"},
            {"filing_number": "UCC-2024-CA-00104", "debtor_name": "SMITH & JONES LLC", "secured_party": "Community Bank", "collateral": "All assets", "filing_date": "2024-04-05", "status": "terminated", "debtor_address": "789 Elm Blvd, San Diego, CA 92101", "debtor_ein": "55-1234567"},
            {"filing_number": "UCC-2024-CA-00105", "debtor_name": "ACME CORP DBA ACME WIDGETS", "secured_party": "Second Regional Bank", "collateral": "Intellectual property and patents", "filing_date": "2024-05-01", "status": "active", "debtor_address": "123 Main St, Los Angeles, CA 90001", "debtor_ein": "12-3456789"},
        ],
    },
    "BATCH-002": {
        "batch_id": "BATCH-002",
        "source": "secretary_of_state_NY",
        "format": "json",
        "filing_count": 4,
        "filings": [
            {"filing_number": "UCC-2024-NY-00201", "debtor_name": "APEX MANUFACTURING CORP", "secured_party": "MetroBank", "collateral": "Manufacturing equipment", "filing_date": "2024-01-20", "status": "active", "debtor_address": "100 Broadway, New York, NY 10001", "debtor_ein": "33-4455667"},
            {"filing_number": "UCC-2024-NY-00202", "debtor_name": "Apex Manufacturing Corporation", "secured_party": "MetroBank", "collateral": "Accounts receivable and inventory", "filing_date": "2024-03-15", "status": "active", "debtor_address": "100 Broadway, New York, NY 10001", "debtor_ein": "33-4455667"},
            {"filing_number": "UCC-2024-NY-00203", "debtor_name": "BROOKLYN STEEL WORKS", "secured_party": "Industrial Finance Corp", "collateral": "Steel inventory, raw materials", "filing_date": "2024-04-10", "status": "active", "debtor_address": "500 Industrial Blvd, Brooklyn, NY 11201", "debtor_ein": "44-5566778"},
            {"filing_number": "UCC-2024-NY-00204", "debtor_name": "TECH INNOVATIONS LLC", "secured_party": "Silicon Valley Bank", "collateral": "Software licenses, IP", "filing_date": "2024-05-20", "status": "active", "debtor_address": "200 Park Ave, New York, NY 10166", "debtor_ein": "66-7788990"},
        ],
    },
    "BATCH-003": {
        "batch_id": "BATCH-003",
        "source": "secretary_of_state_TX",
        "format": "xml",
        "filing_count": 3,
        "filings": [
            {"filing_number": "UCC-2024-TX-00301", "debtor_name": "LONE STAR ENERGY LLC", "secured_party": "Texas Capital Bank", "collateral": "Oil and gas extraction equipment, mineral rights", "filing_date": "2024-02-01", "status": "active", "debtor_address": "1000 Energy Plaza, Houston, TX 77001", "debtor_ein": "77-8899001"},
            {"filing_number": "UCC-2024-TX-00302", "debtor_name": "Lone Star Energy, L.L.C.", "secured_party": "Texas Capital Bank", "collateral": "Pipeline infrastructure", "filing_date": "2024-06-01", "status": "active", "debtor_address": "1000 Energy Plaza, Houston, TX 77001", "debtor_ein": "77-8899001"},
            {"filing_number": "UCC-2024-TX-00303", "debtor_name": "DALLAS FREIGHT SERVICES", "secured_party": "Southwest Lending", "collateral": "Fleet vehicles, trailers", "filing_date": "2024-03-15", "status": "active", "debtor_address": "2500 Commerce St, Dallas, TX 75201", "debtor_ein": "88-9900112"},
        ],
    },
    # --- Edge case: malformed records ---
    "BATCH-004": {
        "batch_id": "BATCH-004",
        "source": "secretary_of_state_FL",
        "format": "csv",
        "filing_count": 3,
        "filings": [
            {"filing_number": "UCC-2024-FL-00401", "debtor_name": "", "secured_party": "Florida Bank", "collateral": "Equipment", "filing_date": "2024-03-01", "status": "active"},
            {"filing_number": "", "debtor_name": "SUNSHINE CORP", "secured_party": "Florida Bank", "collateral": "Inventory", "filing_date": "2024-03-02", "status": "active"},
            {"filing_number": "UCC-2024-FL-00403", "debtor_name": "MIAMI IMPORTS LLC", "secured_party": "Florida Bank", "collateral": "All assets", "filing_date": "invalid-date", "status": "active"},
        ],
    },
    # --- Edge case: duplicate filing numbers ---
    "BATCH-005": {
        "batch_id": "BATCH-005",
        "source": "secretary_of_state_CA",
        "format": "csv",
        "filing_count": 2,
        "filings": [
            {"filing_number": "UCC-2024-CA-00101", "debtor_name": "ACME CORP", "secured_party": "First National Bank", "collateral": "All inventory", "filing_date": "2024-01-15", "status": "active"},
            {"filing_number": "UCC-2024-CA-00101", "debtor_name": "ACME CORP", "secured_party": "First National Bank", "collateral": "All inventory", "filing_date": "2024-01-15", "status": "active"},
        ],
    },
    # --- Edge case: PII in collateral description ---
    "BATCH-006": {
        "batch_id": "BATCH-006",
        "source": "secretary_of_state_IL",
        "format": "json",
        "filing_count": 2,
        "filings": [
            {"filing_number": "UCC-2024-IL-00601", "debtor_name": "MIDWEST SUPPLY CO", "secured_party": "Chicago Savings Bank", "collateral": "All assets. Contact: John Doe SSN 123-45-6789", "filing_date": "2024-04-01", "status": "active", "debtor_address": "300 State St, Chicago, IL 60601"},
            {"filing_number": "UCC-2024-IL-00602", "debtor_name": "WINDY CITY LOGISTICS", "secured_party": "Lake Shore Credit", "collateral": "Fleet vehicles. Owner DOB: 05/15/1970, DL: D123-4567-8901", "filing_date": "2024-04-15", "status": "active", "debtor_address": "400 Michigan Ave, Chicago, IL 60611"},
        ],
    },
    "BATCH-007": {
        "batch_id": "BATCH-007",
        "source": "secretary_of_state_OH",
        "format": "csv",
        "filing_count": 2,
        "filings": [
            {"filing_number": "UCC-2024-OH-00701", "debtor_name": "GREAT LAKES MFG INC", "secured_party": "Ohio First Bank", "collateral": "Manufacturing equipment", "filing_date": "2024-05-01", "status": "active", "debtor_address": "600 Lake Rd, Cleveland, OH 44101", "debtor_ein": "22-3344556"},
            {"filing_number": "UCC-2024-OH-00702", "debtor_name": "Great Lakes Manufacturing, Inc.", "secured_party": "Ohio First Bank", "collateral": "Accounts receivable", "filing_date": "2024-06-15", "status": "active", "debtor_address": "600 Lake Road, Cleveland, OH 44101", "debtor_ein": "22-3344556"},
        ],
    },
    "BATCH-008": {
        "batch_id": "BATCH-008",
        "source": "secretary_of_state_WA",
        "format": "json",
        "filing_count": 2,
        "filings": [
            {"filing_number": "UCC-2024-WA-00801", "debtor_name": "NORTHWEST TIMBER CO", "secured_party": "Pacific Northwest Bank", "collateral": "Timber inventory, logging equipment", "filing_date": "2024-02-15", "status": "active", "debtor_address": "800 Forest Rd, Seattle, WA 98101"},
            {"filing_number": "UCC-2024-WA-00802", "debtor_name": "CASCADE TECHNOLOGIES", "secured_party": "Tech Lending Partners", "collateral": "Server infrastructure, software IP", "filing_date": "2024-03-20", "status": "active", "debtor_address": "900 Tech Blvd, Redmond, WA 98052"},
        ],
    },
    # --- Edge case: unknown format ---
    "BATCH-009": {
        "batch_id": "BATCH-009",
        "source": "secretary_of_state_NV",
        "format": "xlsx",
        "filing_count": 1,
        "filings": [
            {"filing_number": "UCC-2024-NV-00901", "debtor_name": "DESERT SOLAR LLC", "secured_party": "Green Energy Fund", "collateral": "Solar panels", "filing_date": "2024-06-01", "status": "active"},
        ],
    },
    "BATCH-010": {"batch_id": "BATCH-010", "source": "secretary_of_state_CO", "format": "csv", "filing_count": 1, "filings": [{"filing_number": "UCC-2024-CO-01001", "debtor_name": "ROCKY MOUNTAIN MINING", "secured_party": "Colorado National Bank", "collateral": "Mining equipment, mineral rights", "filing_date": "2024-04-20", "status": "active", "debtor_address": "1200 Mine Rd, Denver, CO 80201", "debtor_ein": "99-0011223"}]},
    "BATCH-011": {"batch_id": "BATCH-011", "source": "secretary_of_state_GA", "format": "csv", "filing_count": 1, "filings": [{"filing_number": "UCC-2024-GA-01101", "debtor_name": "PEACHTREE LOGISTICS", "secured_party": "Atlanta Business Credit", "collateral": "Warehouse inventory, delivery fleet", "filing_date": "2024-05-10", "status": "active", "debtor_address": "1500 Peachtree St, Atlanta, GA 30309"}]},
    "BATCH-012": {"batch_id": "BATCH-012", "source": "secretary_of_state_PA", "format": "json", "filing_count": 1, "filings": [{"filing_number": "UCC-2024-PA-01201", "debtor_name": "LIBERTY BELL CONSTRUCTION", "secured_party": "Keystone Savings", "collateral": "Construction equipment, vehicles", "filing_date": "2024-06-05", "status": "active", "debtor_address": "1776 Freedom Ln, Philadelphia, PA 19101"}]},
    "BATCH-013": {"batch_id": "BATCH-013", "source": "secretary_of_state_MI", "format": "csv", "filing_count": 1, "filings": [{"filing_number": "UCC-2024-MI-01301", "debtor_name": "MOTOR CITY PARTS INC", "secured_party": "Detroit Industrial Bank", "collateral": "Auto parts inventory", "filing_date": "2024-03-25", "status": "active", "debtor_address": "2000 Auto Dr, Detroit, MI 48201", "debtor_ein": "11-2233445"}]},
    "BATCH-014": {"batch_id": "BATCH-014", "source": "secretary_of_state_MA", "format": "json", "filing_count": 1, "filings": [{"filing_number": "UCC-2024-MA-01401", "debtor_name": "BOSTON BIOTECH LLC", "secured_party": "Innovation Capital", "collateral": "Lab equipment, patents, IP portfolio", "filing_date": "2024-07-01", "status": "active", "debtor_address": "100 Kendall Sq, Cambridge, MA 02142"}]},
    "BATCH-015": {"batch_id": "BATCH-015", "source": "secretary_of_state_AZ", "format": "csv", "filing_count": 1, "filings": [{"filing_number": "UCC-2024-AZ-01501", "debtor_name": "DESERT VALLEY FARMS", "secured_party": "Agricultural Credit Union", "collateral": "Farm equipment, crop inventory", "filing_date": "2024-05-15", "status": "active", "debtor_address": "3000 Farm Rd, Phoenix, AZ 85001"}]},
    "BATCH-016": {"batch_id": "BATCH-016", "source": "secretary_of_state_MN", "format": "csv", "filing_count": 1, "filings": [{"filing_number": "UCC-2024-MN-01601", "debtor_name": "TWIN CITIES MEDICAL SUPPLY", "secured_party": "Northern Star Bank", "collateral": "Medical equipment and supplies", "filing_date": "2024-06-20", "status": "active", "debtor_address": "500 University Ave, Minneapolis, MN 55401"}]},
}


# ---------------------------------------------------------------------------
# Entity Registry (canonical entity records)
# ---------------------------------------------------------------------------
ENTITY_REGISTRY = {
    "ENT-001": {"entity_id": "ENT-001", "canonical_name": "ACME CORPORATION", "aliases": ["ACME CORP", "ACME CORP DBA ACME WIDGETS", "Acme Corporation"], "ein": "12-3456789", "state": "CA", "city": "Los Angeles", "risk_tier": "medium"},
    "ENT-002": {"entity_id": "ENT-002", "canonical_name": "PACIFIC COAST BUILDERS INC", "aliases": ["PACIFIC COAST BUILDERS INC"], "ein": "98-7654321", "state": "CA", "city": "San Francisco", "risk_tier": "low"},
    "ENT-003": {"entity_id": "ENT-003", "canonical_name": "APEX MANUFACTURING CORPORATION", "aliases": ["APEX MANUFACTURING CORP", "Apex Manufacturing Corporation", "APEX MFG CORP"], "ein": "33-4455667", "state": "NY", "city": "New York", "risk_tier": "low"},
    "ENT-004": {"entity_id": "ENT-004", "canonical_name": "LONE STAR ENERGY LLC", "aliases": ["LONE STAR ENERGY LLC", "Lone Star Energy, L.L.C."], "ein": "77-8899001", "state": "TX", "city": "Houston", "risk_tier": "high"},
    "ENT-005": {"entity_id": "ENT-005", "canonical_name": "GREAT LAKES MANUFACTURING INC", "aliases": ["GREAT LAKES MFG INC", "Great Lakes Manufacturing, Inc."], "ein": "22-3344556", "state": "OH", "city": "Cleveland", "risk_tier": "low"},
}


# ---------------------------------------------------------------------------
# Collateral Classification Taxonomy
# ---------------------------------------------------------------------------
COLLATERAL_TYPES = {
    "inventory": ["inventory", "stock", "goods", "raw materials", "supplies", "crop inventory", "auto parts inventory"],
    "equipment": ["equipment", "machinery", "vehicles", "fleet", "trailers", "construction equipment", "manufacturing equipment", "mining equipment", "logging equipment", "farm equipment", "lab equipment", "server infrastructure", "solar panels"],
    "receivables": ["accounts receivable", "receivables", "notes receivable"],
    "intellectual_property": ["intellectual property", "patents", "IP", "software licenses", "IP portfolio", "software IP"],
    "real_property": ["mineral rights", "pipeline infrastructure", "timber"],
    "general_intangibles": ["all assets", "general intangibles"],
}


# ---------------------------------------------------------------------------
# Quality Rules
# ---------------------------------------------------------------------------
QUALITY_RULES = {
    "filing_number_required": {"description": "Filing number must be non-empty", "severity": "critical"},
    "debtor_name_required": {"description": "Debtor name must be non-empty", "severity": "critical"},
    "valid_date_format": {"description": "Filing date must be YYYY-MM-DD format", "severity": "high"},
    "no_pii_in_collateral": {"description": "Collateral description must not contain PII (SSN, DOB, DL)", "severity": "critical"},
    "no_duplicate_filings": {"description": "No duplicate filing numbers within a batch", "severity": "high"},
    "supported_format": {"description": "File format must be csv, json, or xml", "severity": "medium"},
}
