"""
M04 Lab -- Step 3: Validation with Pydantic (SOLUTION)
=======================================================
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
MODEL = "claude-sonnet-4-6"

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
    """Extract structured filing data using tool_use (from Step 2)."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=[EXTRACT_TOOL],
        tool_choice={"type": "tool", "name": "extract_filing_data"},
        messages=[
            {
                "role": "user",
                "content": (
                    "Extract the structured filing data from this UCC filing description:\n\n"
                    f"{text}"
                ),
            }
        ],
    )

    for block in response.content:
        if block.type == "tool_use":
            return block.input

    raise RuntimeError(
        "No tool_use block found in response. "
        "Ensure tool_choice is set to force tool use."
    )


def extract_and_validate(text: str) -> UCCFiling:
    """
    Extract structured data and validate it with Pydantic.

    Returns a validated UCCFiling instance.
    Raises ValidationError if the extracted data fails validation.
    """
    raw_data = extract_with_tool_use(text)
    return UCCFiling(**raw_data)


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
        # Expect this branch from a capable model, and read it as the lesson
        # rather than as a surprise. The input says "sometime in 2024", "maybe
        # New York" and "the filing number is unknown" -- yet a schema-valid
        # object comes back with a precise filing_date and a definite state.
        # Nothing was validated away because nothing was malformed. It was
        # invented.
        #
        # A schema checks SHAPE, not TRUTH. A confident fabrication satisfies
        # every type, enum and regex you can write, so "we use structured output,
        # therefore the data is reliable" does not follow. Structured output
        # makes data parseable; grounding it is a separate job.
        print("[VALIDATION PASSED] — and that is the point:")
        print(f"  Got: {filing.model_dump_json(indent=2)}")
        print()
        vague = {
            "filing_date": "the input said only 'sometime in 2024'",
            "debtor_state": "the input said 'maybe New York'",
            "debtor_name": "the input offered two spellings; one was chosen",
        }
        for field, why in vague.items():
            value = getattr(filing, field, None)
            if value not in (None, "", "<UNKNOWN>"):
                print(f"  invented  {field} = {value!r}  ({why})")
        print()
        print("  Defence: make uncertainty representable, then validate THAT —")
        print("  an Optional field the model may leave null, or an explicit")
        print("  'unknown' sentinel, so a gap can be stated instead of guessed.")
    except ValidationError as e:
        # More literal models do refuse here. That is the other half of the
        # lesson: whether invention happens is a property of the model, not of
        # the schema, so it is not something to build a guarantee on.
        print("[VALIDATION FAILED] This model declined to invent the missing fields:")
        for error in e.errors():
            print(f"  - {error['loc'][0]}: {error['msg']}")
    except Exception as e:
        print(f"[ERROR] {e}")

    print(f"\n{'=' * 70}")
    print("Step 3 complete! All exercises done.")
    print("=" * 70)
