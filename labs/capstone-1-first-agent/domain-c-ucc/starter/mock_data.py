"""
Mock UCC (Uniform Commercial Code) Filing Records
=====================================================
This module contains simulated UCC-1 financing statement data for the
UCC Filing Lookup Agent. Each record represents a UCC-1 filing registered
with a Secretary of State's office.

In production, this data would come from a Secretary of State's filing
database, accessed via bulk data exports or proprietary search APIs
(e.g., those offered by CSC, CT Corporation, or state-level portals).

Key terminology:
- Debtor: The entity that owes money or has pledged collateral
- Secured Party: The lender or creditor who holds a security interest
- Collateral: The assets pledged against the debt
- Lapse Date: When the filing expires (typically 5 years after filing)
- Continuation: A filing that extends the original UCC-1 for another 5 years
- Amendment: A filing that modifies the original UCC-1
"""

UCC_FILINGS = {
    "2024-0194827": {
        "filing_number": "2024-0194827",
        "filing_type": "UCC-1",
        "status": "active",
        "filing_date": "2024-02-15",
        "lapse_date": "2029-02-15",
        "state": "DE",
        "filing_office": "Delaware Division of Corporations",
        "debtor": {
            "name": "Meridian Logistics Holdings LLC",
            "address": "1209 Orange Street, Wilmington, DE 19801",
            "organization_type": "LLC",
            "jurisdiction": "Delaware",
            "org_id": "DE-LLC-7714829",
        },
        "secured_party": {
            "name": "JPMorgan Chase Bank, N.A.",
            "address": "383 Madison Avenue, New York, NY 10179",
        },
        "collateral_description": "All accounts, chattel paper, deposit accounts, equipment, general intangibles, instruments, inventory, investment property, letter-of-credit rights, and all proceeds and products thereof. Includes all after-acquired property of the same types.",
        "amendments": [],
        "continuation_filed": False,
        "document_pages": 4,
    },
    "2023-0087145": {
        "filing_number": "2023-0087145",
        "filing_type": "UCC-1",
        "status": "active",
        "filing_date": "2023-06-20",
        "lapse_date": "2028-06-20",
        "state": "DE",
        "filing_office": "Delaware Division of Corporations",
        "debtor": {
            "name": "Meridian Fleet Services Inc.",
            "address": "2711 Centerville Road, Suite 400, Wilmington, DE 19808",
            "organization_type": "Corporation",
            "jurisdiction": "Delaware",
            "org_id": "DE-CORP-5531990",
        },
        "secured_party": {
            "name": "Wells Fargo Equipment Finance, Inc.",
            "address": "800 Walnut Street, Des Moines, IA 50309",
        },
        "collateral_description": "All equipment and fixtures now owned or hereafter acquired, specifically including: (i) 47 Freightliner Cascadia Class 8 tractors, VINs listed in Schedule A attached hereto; (ii) 85 Wabash DuraPlate dry van trailers; (iii) all telematics and GPS equipment installed therein; and all proceeds, insurance, and products thereof.",
        "amendments": [
            {
                "amendment_number": "2024-0012883",
                "amendment_date": "2024-01-10",
                "amendment_type": "Collateral Amendment",
                "description": "Added 12 additional Freightliner Cascadia tractors (VINs in Schedule B) and 20 additional dry van trailers to collateral description.",
            },
        ],
        "continuation_filed": False,
        "document_pages": 8,
    },
    "2019-0334521": {
        "filing_number": "2019-0334521",
        "filing_type": "UCC-1",
        "status": "lapsed",
        "filing_date": "2019-08-12",
        "lapse_date": "2024-08-12",
        "state": "NY",
        "filing_office": "New York Department of State",
        "debtor": {
            "name": "Brightstone Capital Partners LLC",
            "address": "125 Park Avenue, 25th Floor, New York, NY 10017",
            "organization_type": "LLC",
            "jurisdiction": "Delaware",
            "org_id": "DE-LLC-6290134",
        },
        "secured_party": {
            "name": "Bank of America, N.A.",
            "address": "100 North Tryon Street, Charlotte, NC 28255",
        },
        "collateral_description": "All assets of the Debtor, including but not limited to: accounts, inventory, equipment, general intangibles (including payment intangibles and software), instruments, documents, chattel paper, deposit accounts, investment property, commercial tort claims, and all proceeds thereof.",
        "amendments": [],
        "continuation_filed": False,
        "document_pages": 3,
    },
    "2022-0451208": {
        "filing_number": "2022-0451208",
        "filing_type": "UCC-1",
        "status": "active",
        "filing_date": "2022-03-28",
        "lapse_date": "2027-03-28",
        "state": "TX",
        "filing_office": "Texas Secretary of State",
        "debtor": {
            "name": "Lone Star Fabrication & Welding Inc.",
            "address": "4500 Industrial Blvd, Houston, TX 77015",
            "organization_type": "Corporation",
            "jurisdiction": "Texas",
            "org_id": "TX-CORP-0812445509",
        },
        "secured_party": {
            "name": "Caterpillar Financial Services Corp.",
            "address": "2120 West End Avenue, Nashville, TN 37203",
        },
        "collateral_description": "Specific equipment: (1) Caterpillar 320 GC Hydraulic Excavator, S/N CAT0320VCXYZ4321; (2) Caterpillar D6 Dozer, S/N CAT00D6HABCD5678; (3) Caterpillar 950 GC Wheel Loader, S/N CAT0950GEFGH9101. Including all attachments, accessories, accessions, and replacements. All proceeds and insurance thereof.",
        "amendments": [],
        "continuation_filed": False,
        "document_pages": 3,
    },
    "2020-0112890": {
        "filing_number": "2020-0112890",
        "filing_type": "UCC-1",
        "status": "active",
        "filing_date": "2020-11-05",
        "lapse_date": "2025-11-05",
        "state": "CA",
        "filing_office": "California Secretary of State",
        "debtor": {
            "name": "Pacific Rim Imports & Distribution LLC",
            "address": "2100 E. Willow Street, Signal Hill, CA 90755",
            "organization_type": "LLC",
            "jurisdiction": "California",
            "org_id": "CA-LLC-202100312987",
        },
        "secured_party": {
            "name": "East West Bank",
            "address": "135 N. Los Robles Ave, Pasadena, CA 91101",
        },
        "collateral_description": "All inventory now owned or hereafter acquired, including goods held for sale or lease, raw materials, work in process, and finished goods. All accounts receivable and rights to payment arising from the sale of inventory. All proceeds thereof.",
        "amendments": [
            {
                "amendment_number": "2023-0045612",
                "amendment_date": "2023-03-15",
                "amendment_type": "Assignment",
                "description": "Partial assignment of secured party interest from East West Bank to Pacific Western Bank for accounts receivable portion of collateral.",
            },
        ],
        "continuation_filed": True,
        "continuation_date": "2025-09-01",
        "document_pages": 5,
    },
    "2021-0298374": {
        "filing_number": "2021-0298374",
        "filing_type": "UCC-1",
        "status": "terminated",
        "filing_date": "2021-04-18",
        "lapse_date": "2026-04-18",
        "termination_date": "2024-01-22",
        "state": "IL",
        "filing_office": "Illinois Secretary of State",
        "debtor": {
            "name": "Great Lakes Brewing Collective Inc.",
            "address": "811 W. Fulton Market, Chicago, IL 60607",
            "organization_type": "Corporation",
            "jurisdiction": "Illinois",
            "org_id": "IL-CORP-08127445",
        },
        "secured_party": {
            "name": "BMO Harris Bank N.A.",
            "address": "111 W. Monroe Street, Chicago, IL 60603",
        },
        "collateral_description": "All equipment, including but not limited to: brewing tanks, fermentation vessels, kegging lines, canning lines, cold storage units, and delivery vehicles. All inventory of raw materials (hops, malt, yeast) and finished product. All proceeds thereof.",
        "amendments": [
            {
                "amendment_number": "2024-0009123",
                "amendment_date": "2024-01-22",
                "amendment_type": "Termination",
                "description": "UCC-3 Termination filed. Underlying loan paid in full. All security interests released.",
            },
        ],
        "continuation_filed": False,
        "document_pages": 4,
    },
    "2024-0223901": {
        "filing_number": "2024-0223901",
        "filing_type": "UCC-1",
        "status": "active",
        "filing_date": "2024-05-02",
        "lapse_date": "2029-05-02",
        "state": "DE",
        "filing_office": "Delaware Division of Corporations",
        "debtor": {
            "name": "Pinnacle Health Systems Group LLC",
            "address": "251 Little Falls Drive, Wilmington, DE 19808",
            "organization_type": "LLC",
            "jurisdiction": "Delaware",
            "org_id": "DE-LLC-8301456",
        },
        "secured_party": {
            "name": "Citibank, N.A., as Administrative Agent",
            "address": "388 Greenwich Street, New York, NY 10013",
        },
        "collateral_description": "All assets of the Debtor and each Guarantor, including without limitation: accounts, chattel paper, commercial tort claims, deposit accounts, documents, equipment, fixtures, general intangibles, goods, instruments, intellectual property, inventory, investment property, letter-of-credit rights, money, and all proceeds of the foregoing. This filing is filed as a precautionary filing and is not an admission that the transactions described herein constitute a secured transaction.",
        "amendments": [],
        "continuation_filed": False,
        "document_pages": 6,
    },
    "2023-0178432": {
        "filing_number": "2023-0178432",
        "filing_type": "UCC-1",
        "status": "active",
        "filing_date": "2023-09-14",
        "lapse_date": "2028-09-14",
        "state": "FL",
        "filing_office": "Florida Secured Transaction Registry",
        "debtor": {
            "name": "SunCoast Marine Services LLC",
            "address": "1500 SE 17th Street, Fort Lauderdale, FL 33316",
            "organization_type": "LLC",
            "jurisdiction": "Florida",
            "org_id": "FL-LLC-L23000445512",
        },
        "secured_party": {
            "name": "Truist Bank",
            "address": "214 N. Tryon Street, Charlotte, NC 28202",
        },
        "collateral_description": "Specific vessels: (1) 2022 Yellowfin 54 Offshore, HIN YFN54XXX2022A001; (2) 2023 Boston Whaler 420 Outrage, HIN BWC42XXX2023B012; (3) All marine engines, electronics, navigation equipment, and trailers associated with the above vessels. All insurance proceeds thereof.",
        "amendments": [],
        "continuation_filed": False,
        "document_pages": 4,
    },
    "2018-0445210": {
        "filing_number": "2018-0445210",
        "filing_type": "UCC-1",
        "status": "lapsed",
        "filing_date": "2018-12-01",
        "lapse_date": "2023-12-01",
        "state": "NY",
        "filing_office": "New York Department of State",
        "debtor": {
            "name": "Hudson Valley Agri-Tech Corp.",
            "address": "45 Market Street, Poughkeepsie, NY 12601",
            "organization_type": "Corporation",
            "jurisdiction": "New York",
            "org_id": "NY-CORP-5467123",
        },
        "secured_party": {
            "name": "Farm Credit East, ACA",
            "address": "240 South Road, Enfield, CT 06082",
        },
        "collateral_description": "All farm products, including crops (grown and growing), livestock, and supplies used or produced in farming operations. All equipment used in farming operations including tractors, harvesters, irrigation systems, and greenhouse structures. All accounts and general intangibles arising from the sale of farm products. All proceeds thereof.",
        "amendments": [],
        "continuation_filed": False,
        "document_pages": 3,
    },
    "2024-0301578": {
        "filing_number": "2024-0301578",
        "filing_type": "UCC-1",
        "status": "active",
        "filing_date": "2024-08-22",
        "lapse_date": "2029-08-22",
        "state": "TX",
        "filing_office": "Texas Secretary of State",
        "debtor": {
            "name": "Permian Basin Energy Services LLC",
            "address": "300 N. Marienfeld Street, Suite 800, Midland, TX 79701",
            "organization_type": "LLC",
            "jurisdiction": "Texas",
            "org_id": "TX-LLC-0803991287",
        },
        "secured_party": {
            "name": "Frost Bank",
            "address": "100 W. Houston Street, San Antonio, TX 78205",
        },
        "collateral_description": "All equipment related to oilfield services, including: coiled tubing units, pressure pumping equipment, wireline units, workover rigs, fluid hauling trucks and tankers, and all related tools, parts, and accessories. All accounts receivable arising from oilfield services contracts. All proceeds and insurance thereof.",
        "amendments": [
            {
                "amendment_number": "2024-0401223",
                "amendment_date": "2024-10-15",
                "amendment_type": "Collateral Amendment",
                "description": "Added newly acquired equipment: 2 additional coiled tubing units (S/N CT-2024-001, CT-2024-002) and 4 fluid hauling trucks (VINs listed in Schedule C).",
            },
        ],
        "continuation_filed": False,
        "document_pages": 7,
    },
}
