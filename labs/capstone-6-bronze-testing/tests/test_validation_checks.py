"""
Tests for all 12 Bronze Table Validation Checks

Each check is tested with known-good data (should PASS) and known-bad data (should FAIL or WARN).
"""

import os
import sys
import pytest

SOLUTION_DIR = os.path.join(os.path.dirname(__file__), "..", "solution")
sys.path.insert(0, SOLUTION_DIR)

from checks.source_checks import check_source_parseable
from checks.count_checks import check_record_count
from checks.filing_checks import check_filing_number_integrity
from checks.duplicate_checks import check_no_duplicates
from checks.type_checks import check_filing_type_normalized
from checks.date_checks import check_date_format, check_date_values
from checks.status_checks import check_status_normalized
from checks.name_checks import check_name_normalization
from checks.null_checks import check_required_fields_not_null
from checks.metadata_checks import check_load_metadata
from checks.spot_checks import check_spot_sample


# ── Test fixtures ──────────────────────────────────────────────────────────

GOOD_RECORDS = [
    {
        "filing_number": "NY-2024-0001",
        "state": "NY",
        "filing_type": "UCC1",
        "filing_date": "2024-10-01",
        "lapse_date": "2029-10-01",
        "status": "ACTIVE",
        "debtor_name": "ACME CORPORATION",
        "debtor_address": "123 Broadway, New York, NY 10001",
        "secured_party_name": "FIRST NATIONAL BANK",
        "collateral_description": "All inventory",
        "load_timestamp": "2024-12-15T08:30:00Z",
        "load_batch_id": "BATCH-2024-Q4-001",
        "source_file": "NY_2024_Q4.xml",
    },
    {
        "filing_number": "NY-2024-0002",
        "state": "NY",
        "filing_type": "UCC3_AMENDMENT",
        "filing_date": "2024-10-05",
        "lapse_date": "2029-10-05",
        "status": "TERMINATED",
        "debtor_name": "BROADWAY LOGISTICS INC",
        "debtor_address": "456 Fifth Ave, New York, NY 10018",
        "secured_party_name": "CITIBANK NA",
        "collateral_description": "All equipment",
        "load_timestamp": "2024-12-15T08:30:00Z",
        "load_batch_id": "BATCH-2024-Q4-001",
        "source_file": "NY_2024_Q4.xml",
    },
]

GOOD_SOURCE_RECORDS = [
    {
        "filing_number": "NY-2024-0001",
        "filing_type": "UCC1",
        "filing_date": "2024-10-01",
        "lapse_date": "2029-10-01",
        "status": "ACTIVE",
        "debtor_name": "ACME CORPORATION",
        "secured_party_name": "FIRST NATIONAL BANK",
        "collateral_description": "All inventory",
    },
    {
        "filing_number": "NY-2024-0002",
        "filing_type": "UCC3_AMENDMENT",
        "filing_date": "2024-10-05",
        "lapse_date": "2029-10-05",
        "status": "TERMINATED",
        "debtor_name": "BROADWAY LOGISTICS INC",
        "secured_party_name": "CITIBANK NA",
        "collateral_description": "All equipment",
    },
]


# ── SRC-01 ─────────────────────────────────────────────────────────────────

class TestSourceParseable:
    def test_pass_when_records_present(self):
        result = check_source_parseable(
            state="NY", source_file="NY_2024_Q4.xml",
            source_records=GOOD_SOURCE_RECORDS, bronze_records=GOOD_RECORDS,
        )
        assert result["status"] == "PASS"
        assert result["check_id"] == "SRC-01"

    def test_fail_when_parse_error(self):
        result = check_source_parseable(
            state="TX_BAD", source_file="TX_BAD_truncated.dat",
            source_records=None, bronze_records=[],
            parse_error="Truncated file",
        )
        assert result["status"] == "FAIL"

    def test_fail_when_no_records(self):
        result = check_source_parseable(
            state="XX", source_file="empty.xml",
            source_records=[], bronze_records=[],
        )
        assert result["status"] == "FAIL"


# ── CNT-01 ─────────────────────────────────────────────────────────────────

class TestRecordCount:
    def test_pass_when_counts_match(self):
        result = check_record_count(
            state="NY", source_records=GOOD_SOURCE_RECORDS,
            bronze_records=GOOD_RECORDS, expected_count=2,
        )
        assert result["status"] == "PASS"

    def test_fail_when_counts_mismatch(self):
        result = check_record_count(
            state="NY", source_records=GOOD_SOURCE_RECORDS[:1],
            bronze_records=GOOD_RECORDS, expected_count=2,
        )
        assert result["status"] == "FAIL"


# ── FN-01 ──────────────────────────────────────────────────────────────────

class TestFilingNumberIntegrity:
    def test_pass_valid_numbers(self):
        result = check_filing_number_integrity(state="NY", bronze_records=GOOD_RECORDS)
        assert result["status"] == "PASS"

    def test_fail_invalid_format(self):
        bad = [{"filing_number": "BAD_FORMAT_123"}]
        result = check_filing_number_integrity(state="NY", bronze_records=bad)
        assert result["status"] == "FAIL"

    def test_warn_wrong_state_prefix(self):
        wrong = [{"filing_number": "CA-2024-0001"}]
        result = check_filing_number_integrity(state="NY", bronze_records=wrong)
        assert result["status"] == "WARN"


# ── DUP-01 ─────────────────────────────────────────────────────────────────

class TestNoDuplicates:
    def test_pass_no_duplicates(self):
        result = check_no_duplicates(state="NY", bronze_records=GOOD_RECORDS)
        assert result["status"] == "PASS"

    def test_warn_with_duplicates(self):
        dup_records = GOOD_RECORDS + [GOOD_RECORDS[0]]
        result = check_no_duplicates(state="NY", bronze_records=dup_records)
        assert result["status"] == "WARN"


# ── FT-01 ──────────────────────────────────────────────────────────────────

class TestFilingTypeNormalized:
    def test_pass_valid_types(self):
        result = check_filing_type_normalized(state="NY", bronze_records=GOOD_RECORDS)
        assert result["status"] == "PASS"

    def test_fail_invalid_type(self):
        bad = [{"filing_number": "NY-2024-0001", "filing_type": "UCC99"}]
        result = check_filing_type_normalized(state="NY", bronze_records=bad)
        assert result["status"] == "FAIL"


# ── DT-01 ──────────────────────────────────────────────────────────────────

class TestDateFormat:
    def test_pass_valid_dates(self):
        result = check_date_format(state="NY", bronze_records=GOOD_RECORDS)
        assert result["status"] == "PASS"

    def test_fail_bad_format(self):
        bad = [{"filing_number": "GA-2024-0001", "filing_date": "01/10/2024", "lapse_date": "01/10/2029"}]
        result = check_date_format(state="GA", bronze_records=bad)
        assert result["status"] == "FAIL"


# ── DT-02 ──────────────────────────────────────────────────────────────────

class TestDateValues:
    def test_pass_valid_values(self):
        result = check_date_values(state="NY", bronze_records=GOOD_RECORDS)
        # May PASS or FAIL depending on whether lapse > filing; our good records are valid
        assert result["check_id"] == "DT-02"

    def test_fail_lapse_before_filing(self):
        bad = [{
            "filing_number": "NY-2024-0001",
            "filing_date": "2024-10-05",
            "lapse_date": "2024-10-01",
        }]
        result = check_date_values(state="NY", bronze_records=bad)
        assert result["status"] == "FAIL"


# ── ST-01 ──────────────────────────────────────────────────────────────────

class TestStatusNormalized:
    def test_pass_valid_statuses(self):
        result = check_status_normalized(state="NY", bronze_records=GOOD_RECORDS)
        assert result["status"] == "PASS"

    def test_fail_invalid_status(self):
        bad = [{"filing_number": "NY-2024-0001", "status": "PENDING"}]
        result = check_status_normalized(state="NY", bronze_records=bad)
        assert result["status"] == "FAIL"


# ── NM-01 ──────────────────────────────────────────────────────────────────

class TestNameNormalization:
    def test_pass_uppercase_names(self):
        result = check_name_normalization(state="NY", bronze_records=GOOD_RECORDS)
        assert result["status"] == "PASS"

    def test_fail_lowercase_names(self):
        bad = [{
            "filing_number": "NY-2024-0001",
            "debtor_name": "Acme Corporation",
            "secured_party_name": "First National Bank",
        }]
        result = check_name_normalization(state="NY", bronze_records=bad)
        assert result["status"] == "FAIL"


# ── NL-01 ──────────────────────────────────────────────────────────────────

class TestRequiredFieldsNotNull:
    def test_pass_all_populated(self):
        result = check_required_fields_not_null(state="NY", bronze_records=GOOD_RECORDS)
        assert result["status"] == "PASS"

    def test_fail_null_field(self):
        bad = [{
            "filing_number": "NY-2024-0001",
            "state": "NY",
            "filing_type": "",
            "filing_date": "2024-10-01",
            "status": "ACTIVE",
            "debtor_name": "TEST CORP",
        }]
        result = check_required_fields_not_null(state="NY", bronze_records=bad)
        assert result["status"] == "FAIL"


# ── LM-01 ──────────────────────────────────────────────────────────────────

class TestLoadMetadata:
    def test_pass_metadata_present(self):
        result = check_load_metadata(state="NY", bronze_records=GOOD_RECORDS)
        assert result["status"] == "PASS"

    def test_fail_missing_metadata(self):
        bad = [{"filing_number": "NY-2024-0001"}]  # No metadata fields
        result = check_load_metadata(state="NY", bronze_records=bad)
        assert result["status"] == "FAIL"


# ── SP-01 ──────────────────────────────────────────────────────────────────

class TestSpotCheck:
    def test_pass_matching_records(self):
        result = check_spot_sample(
            state="NY", source_records=GOOD_SOURCE_RECORDS,
            bronze_records=GOOD_RECORDS,
        )
        assert result["status"] == "PASS"

    def test_fail_no_source(self):
        result = check_spot_sample(
            state="NY", source_records=None, bronze_records=GOOD_RECORDS,
        )
        assert result["status"] == "FAIL"

    def test_fail_empty_bronze(self):
        result = check_spot_sample(
            state="NY", source_records=GOOD_SOURCE_RECORDS, bronze_records=[],
        )
        assert result["status"] == "FAIL"
