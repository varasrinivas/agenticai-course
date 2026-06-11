"""
M04 Lab: Schema and Test Data (shared helper — identical to starter version)
==============================================================================
"""

import json
from typing import Optional

from pydantic import BaseModel


class ContactInfo(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    company: Optional[str] = None
    role: Optional[str] = None


TEST_SIGNATURES = [
    "Best, Jane Smith | jane@acme.com | Acme Corp",
    "John Doe, Senior Engineer at MegaTech\njohn.doe@megatech.io | (555) 234-5678",
    "Cheers,\nDr. Maria García-López, Head of Research\nBioGen International\nmgarcia@biogen.int",
    "— Alex K. | Product @ StartupXYZ | alex@startupxyz.co | they/them",
    "Thanks!\nRobert \"Bob\" Williams III\nChief Financial Officer\nGlobal Finance Partners LLC\nrwilliams@gfp.com\n+1 (212) 555-0199",
]


if __name__ == "__main__":
    print(json.dumps(ContactInfo.model_json_schema(), indent=2))
    print(f"\nTest signatures: {len(TEST_SIGNATURES)}")
