"""
M04 Lab -- Step 2: Tool Use for Guaranteed Structure
=====================================================
Use Claude's tool_use feature to guarantee structured JSON output.
Claude returns data by "calling" a tool with the extracted fields.
"""

import json
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-6"

# ─── Sample freetext filing descriptions (same as Step 1) ────────────────────

FREETEXT_FILINGS = [
    "On March 15, 2024, Greenfield Logistics LLC (a New York LLC located at 450 West 33rd Street, "
    "Suite 800, New York, NY 10001) filed a UCC-1 financing statement with the NY Department of State. "
    "Atlantic Capital Partners (1 Chase Manhattan Plaza, Floor 45, New York, NY 10005) is listed as the "
    "secured party. The collateral covers all accounts receivable, inventory, equipment, and general "
    "intangibles now owned or hereafter acquired by the Debtor.",

    "A UCC-1 was recorded on September 10, 2023 in Texas. The debtor is Lone Star Energy Solutions LP, "
    "a Texas limited partnership headquartered at 1200 Smith Street, Suite 3000, Houston, TX 77002. "
    "Wells Fargo Equipment Finance holds the security interest in specific equipment: three Caterpillar "
    "349F L hydraulic excavators (serial numbers CAT349F-8821, CAT349F-8822, CAT349F-8823) and one "
    "Liebherr LTM 1300-6.2 mobile crane (serial number LTM-DE-90124).",

    "Sunshine Medical Group PA (a Florida professional association at 4500 Biscayne Boulevard, Miami, "
    "FL 33137) filed an amendment (UCC-3) on June 1, 2024 with the FL Secured Transaction Registry. "
    "This amends the original filing UCC-2022-FL-0031456. TD Bank N.A. is the secured party. The "
    "amendment adds medical equipment including two Siemens MAGNETOM Vida 3T MRI systems and one GE "
    "Revolution CT scanner to the existing collateral.",
]

# ─── Tool definition ─────────────────────────────────────────────────────────

EXTRACT_TOOL = {
    "name": "extract_filing_data",
    "description": (
        "Extract structured data from a UCC filing description. "
        "Call this tool with the extracted fields from the provided text."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "filing_type": {
                "type": "string",
                "enum": ["UCC-1", "UCC-3"],
                "description": "The type of UCC filing"
            },
            "filing_date": {
                "type": "string",
                "description": "Filing date in YYYY-MM-DD format"
            },
            "debtor_name": {
                "type": "string",
                "description": "Full legal name of the debtor organization"
            },
            "debtor_type": {
                "type": "string",
                "enum": ["LLC", "Corporation", "Limited Partnership", "Professional Association", "Cooperative", "Sole Proprietorship", "Other"],
                "description": "Type of business organization"
            },
            "debtor_state": {
                "type": "string",
                "description": "State where the filing was made"
            },
            "secured_party": {
                "type": "string",
                "description": "Name of the secured party (lender/creditor)"
            },
            "collateral_type": {
                "type": "string",
                "enum": ["Blanket Lien", "Equipment", "Accounts Receivable", "Inventory", "Intellectual Property", "Real Property", "Agricultural", "Medical Equipment", "Other"],
                "description": "Category of collateral"
            },
            "collateral_description": {
                "type": "string",
                "description": "Brief summary of the collateral covered"
            }
        },
        "required": [
            "filing_type", "filing_date", "debtor_name", "debtor_type",
            "debtor_state", "secured_party", "collateral_type", "collateral_description"
        ]
    }
}


def extract_with_tool_use(text: str) -> dict:
    """
    Extract structured filing data using Claude's tool_use feature.
    This guarantees the output matches the JSON Schema defined in EXTRACT_TOOL.

    Returns a dict with the extracted fields.
    """
    # TODO: Call client.messages.create with:
    #   - model=MODEL
    #   - max_tokens=1024
    #   - tools=[EXTRACT_TOOL]
    #   - tool_choice={"type": "tool", "name": "extract_filing_data"}
    #     (this FORCES Claude to call the tool -- no text response possible)
    #   - messages: a single user message asking Claude to extract filing data
    #     from the provided text
    #
    # Then find the tool_use block in response.content:
    #   for block in response.content:
    #       if block.type == "tool_use":
    #           return block.input  # This is the structured dict
    #
    # If no tool_use block found, raise an error.
    pass


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("M04 Lab -- Step 2: Tool Use for Guaranteed Structure")
    print("=" * 70)

    for i, text in enumerate(FREETEXT_FILINGS, 1):
        print(f"\n{'─' * 70}")
        print(f"Filing {i}:")
        print(f"{'─' * 70}")
        print(f"Input (first 100 chars): {text[:100]}...")
        print()

        try:
            result = extract_with_tool_use(text)
            if result is None:
                print("[INCOMPLETE] Function returned None -- complete the TODO")
            else:
                print("Extracted via tool_use:")
                print(json.dumps(result, indent=2))
                print(f"\n  [OK] All {len(result)} fields present")
        except Exception as e:
            print(f"[ERROR] {e}")

    print(f"\n{'=' * 70}")
    print("Step 2 complete! Next: validated_extractor.py (Step 3)")
    print("=" * 70)
