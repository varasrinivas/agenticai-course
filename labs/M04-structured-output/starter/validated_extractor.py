"""
M04 Lab -- Step 3: Validation with Pydantic
=============================================
Add schema validation to ensure extracted data is not just valid JSON
but semantically correct (valid dates, valid enums, non-empty strings).
"""

import json
import re
from datetime import date

import anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator, ValidationError

load_dotenv()

client = anthropic.Anthropic()
MODEL = "claude-sonnet-4-20250514"

# ─── Sample freetext filing descriptions (same as Steps 1-2) ─────────────────

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

# Edge case -- deliberately ambiguous/malformed
EDGE_CASE_TEXT = (
    "filed sometime in 2024, maybe New York. Debtor could be Smith & Co or Smith and Company. "
    "Collateral: everything? Also the filing number is unknown."
)

# ─── Tool definition (reused from Step 2) ────────────────────────────────────

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


# ─── Pydantic validation model ───────────────────────────────────────────────

VALID_FILING_TYPES = {"UCC-1", "UCC-3"}
VALID_DEBTOR_TYPES = {
    "LLC", "Corporation", "Limited Partnership",
    "Professional Association", "Cooperative", "Sole Proprietorship", "Other"
}
VALID_COLLATERAL_TYPES = {
    "Blanket Lien", "Equipment", "Accounts Receivable", "Inventory",
    "Intellectual Property", "Real Property", "Agricultural", "Medical Equipment", "Other"
}


class UCCFiling(BaseModel):
    """Validated UCC filing data with semantic constraints."""

    filing_type: str = Field(..., description="UCC-1 or UCC-3")
    filing_date: str = Field(..., description="Date in YYYY-MM-DD format")
    debtor_name: str = Field(..., min_length=2, description="Full legal name of debtor")
    debtor_type: str = Field(..., description="Organization type")
    debtor_state: str = Field(..., min_length=2, description="State of filing")
    secured_party: str = Field(..., min_length=2, description="Name of secured party")
    collateral_type: str = Field(..., description="Category of collateral")
    collateral_description: str = Field(..., min_length=5, description="Collateral summary")

    @field_validator("filing_type")
    @classmethod
    def validate_filing_type(cls, v: str) -> str:
        if v not in VALID_FILING_TYPES:
            raise ValueError(f"filing_type must be one of {VALID_FILING_TYPES}, got '{v}'")
        return v

    @field_validator("filing_date")
    @classmethod
    def validate_filing_date(cls, v: str) -> str:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", v):
            raise ValueError(f"filing_date must be YYYY-MM-DD format, got '{v}'")
        # Also validate it is a real date
        try:
            year, month, day = v.split("-")
            date(int(year), int(month), int(day))
        except ValueError:
            raise ValueError(f"filing_date is not a valid calendar date: '{v}'")
        return v

    @field_validator("debtor_type")
    @classmethod
    def validate_debtor_type(cls, v: str) -> str:
        if v not in VALID_DEBTOR_TYPES:
            raise ValueError(f"debtor_type must be one of {VALID_DEBTOR_TYPES}, got '{v}'")
        return v

    @field_validator("collateral_type")
    @classmethod
    def validate_collateral_type(cls, v: str) -> str:
        if v not in VALID_COLLATERAL_TYPES:
            raise ValueError(f"collateral_type must be one of {VALID_COLLATERAL_TYPES}, got '{v}'")
        return v


# ─── Extraction + Validation ─────────────────────────────────────────────────

def extract_with_tool_use(text: str) -> dict:
    """
    Extract structured filing data using tool_use (copied from Step 2).
    You can reuse your Step 2 implementation here.
    """
    # TODO: Implement tool_use extraction (same as Step 2).
    # Call client.messages.create with EXTRACT_TOOL and tool_choice to force tool use.
    # Return the block.input dict from the tool_use response block.
    pass


def extract_and_validate(text: str) -> UCCFiling:
    """
    Extract structured data and validate it with Pydantic.

    Returns a validated UCCFiling instance.
    Raises ValidationError if the extracted data fails validation.
    """
    # TODO:
    #   1. Call extract_with_tool_use(text) to get the raw dict
    #   2. Pass the dict to UCCFiling(**raw_data) to validate
    #   3. Return the validated UCCFiling instance
    #   4. Let ValidationError propagate to the caller (don't catch it here)
    pass


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("M04 Lab -- Step 3: Validation with Pydantic")
    print("=" * 70)

    # --- Test valid filings ---
    for i, text in enumerate(FREETEXT_FILINGS, 1):
        print(f"\n{'─' * 70}")
        print(f"Filing {i} (should PASS validation):")
        print(f"{'─' * 70}")
        print(f"Input (first 100 chars): {text[:100]}...")
        print()

        try:
            filing = extract_and_validate(text)
            if filing is None:
                print("[INCOMPLETE] Function returned None -- complete the TODO")
            else:
                print("[PASS] Validated successfully!")
                print(f"  Filing type:  {filing.filing_type}")
                print(f"  Filing date:  {filing.filing_date}")
                print(f"  Debtor:       {filing.debtor_name} ({filing.debtor_type})")
                print(f"  State:        {filing.debtor_state}")
                print(f"  Secured:      {filing.secured_party}")
                print(f"  Collateral:   {filing.collateral_type}")
                print(f"  Description:  {filing.collateral_description[:80]}...")
        except ValidationError as e:
            print(f"[UNEXPECTED FAIL] Validation error on valid filing:")
            for error in e.errors():
                print(f"  - {error['loc'][0]}: {error['msg']}")
        except Exception as e:
            print(f"[ERROR] {e}")

    # --- Test edge case (should fail validation) ---
    print(f"\n{'─' * 70}")
    print("Edge Case (should FAIL validation):")
    print(f"{'─' * 70}")
    print(f"Input: {EDGE_CASE_TEXT}")
    print()

    try:
        filing = extract_and_validate(EDGE_CASE_TEXT)
        if filing is None:
            print("[INCOMPLETE] Function returned None -- complete the TODO")
        else:
            print("[UNEXPECTED PASS] Edge case should have failed validation!")
            print(f"  Got: {filing.model_dump_json(indent=2)}")
    except ValidationError as e:
        print("[EXPECTED FAIL] Validation caught bad data:")
        for error in e.errors():
            print(f"  - {error['loc'][0]}: {error['msg']}")
    except Exception as e:
        print(f"[ERROR] {e}")

    print(f"\n{'=' * 70}")
    print("Step 3 complete! All exercises done.")
    print("=" * 70)
