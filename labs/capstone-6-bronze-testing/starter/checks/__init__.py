"""
Bronze Table Validation Checks

Each check module implements one or more validation rules against
the Bronze canonical UCC filing table. Checks return a standardized
result dict:

{
    "check_id": "SRC-01",
    "check_name": "Source File Parseable",
    "status": "PASS" | "FAIL" | "WARN",
    "message": "Human-readable summary",
    "details": { ... }  # Check-specific detail payload
}
"""

from .source_checks import check_source_parseable
from .count_checks import check_record_count
from .filing_checks import check_filing_number_integrity
from .duplicate_checks import check_no_duplicates
from .type_checks import check_filing_type_normalized
from .date_checks import check_date_format, check_date_values
from .status_checks import check_status_normalized
from .name_checks import check_name_normalization
from .null_checks import check_required_fields_not_null
from .metadata_checks import check_load_metadata
from .spot_checks import check_spot_sample

ALL_CHECKS = [
    ("SRC-01", "Source File Parseable", check_source_parseable),
    ("CNT-01", "Record Count Match", check_record_count),
    ("FN-01", "Filing Number Integrity", check_filing_number_integrity),
    ("DUP-01", "No Duplicate Filing Numbers", check_no_duplicates),
    ("FT-01", "Filing Type Normalized", check_filing_type_normalized),
    ("DT-01", "Date Format Valid", check_date_format),
    ("DT-02", "Date Values Valid", check_date_values),
    ("ST-01", "Status Normalized", check_status_normalized),
    ("NM-01", "Name Normalization", check_name_normalization),
    ("NL-01", "Required Fields Not Null", check_required_fields_not_null),
    ("LM-01", "Load Metadata Present", check_load_metadata),
    ("SP-01", "Spot Check Sample", check_spot_sample),
]
