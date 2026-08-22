"""The type mapping table.

Fast, deterministic, no database and no API calls -- which is the whole
argument for putting the mechanical part of the mapping in code rather
than leaving it to the prompt. These 40-odd assertions run in
milliseconds and would cost real money and real minutes as model calls.
"""

from __future__ import annotations

import pytest

# The mapping now lives inside the skill that explains it, so the test
# reaches it the same way an agent would: by path, not by package import.
from conftest import load_skill_script

_check_mapping = load_skill_script('oracle-pg-typing', 'check_mapping.py')
Confidence = _check_mapping.Confidence
map_type = _check_mapping.map_type
quote_policy = _check_mapping.quote_policy


# ------------------------------------------------------------- NUMBER
@pytest.mark.parametrize(
    "oracle,expected",
    [
        ("NUMBER(2)", "smallint"),
        ("NUMBER(4,0)", "smallint"),
        ("NUMBER(9)", "integer"),
        ("NUMBER(9,0)", "integer"),
        ("NUMBER(12)", "bigint"),
        ("NUMBER(18,0)", "bigint"),
        ("NUMBER(9,2)", "numeric(9,2)"),
        ("NUMBER(38)", "numeric(38)"),
    ],
)
def test_number_precision_picks_the_right_width(oracle, expected):
    assert map_type(oracle).postgres_type == expected


def test_unconstrained_number_stays_numeric_and_asks_for_a_look():
    mapping = map_type("NUMBER")
    assert mapping.postgres_type == "numeric"
    assert mapping.confidence is Confidence.CHECK_DATA
    assert mapping.needs_review


def test_negative_scale_is_flagged_for_a_human():
    """NUMBER(9,-2) rounds to the nearest hundred. PostgreSQL has no
    equivalent, so this is a design decision, not a translation."""
    mapping = map_type("NUMBER(9,-2)")
    assert mapping.confidence is Confidence.MANUAL


# --------------------------------------------------------------- DATE
def test_oracle_date_becomes_timestamp_not_date():
    """The single most consequential row in the mapping table.

    Oracle DATE carries a time component. Mapping it to `date` compiles,
    loads, and silently truncates every filed_date to midnight -- which
    changes which filings look lapsed. Nothing errors.
    """
    mapping = map_type("DATE")
    assert mapping.postgres_type == "timestamp(0)"
    assert mapping.postgres_type != "date"
    assert "time component" in mapping.reason.lower()


@pytest.mark.parametrize(
    "oracle,expected",
    [
        ("TIMESTAMP", "timestamp"),
        ("TIMESTAMP(6)", "timestamp(6)"),
        ("TIMESTAMP(6) WITH TIME ZONE", "timestamptz(6)"),
        ("TIMESTAMP WITH LOCAL TIME ZONE", "timestamptz"),
    ],
)
def test_timestamp_variants(oracle, expected):
    assert map_type(oracle).postgres_type == expected


def test_local_time_zone_notes_the_behaviour_change():
    mapping = map_type("TIMESTAMP WITH LOCAL TIME ZONE")
    assert mapping.confidence is Confidence.CHECK_DATA
    assert "session" in mapping.reason.lower()


# ---------------------------------------------------------- character
@pytest.mark.parametrize(
    "oracle,expected",
    [
        ("VARCHAR2(60 BYTE)", "varchar(60)"),
        ("VARCHAR2(240 CHAR)", "varchar(240)"),
        ("VARCHAR2(120)", "varchar(120)"),
        ("CHAR(2)", "char(2)"),
    ],
)
def test_character_types(oracle, expected):
    assert map_type(oracle).postgres_type == expected


def test_byte_semantics_are_flagged_but_char_semantics_are_not():
    """VARCHAR2(60 BYTE) and varchar(60) hold different amounts of text
    once the data is not ASCII. That is worth a warning; VARCHAR2(60 CHAR)
    is not."""
    assert map_type("VARCHAR2(60 BYTE)").confidence is Confidence.CHECK_DATA
    assert map_type("VARCHAR2(60 CHAR)").confidence is Confidence.CONFIDENT


# ------------------------------------------------------------- binary
def test_raw16_with_uuid_shaped_samples_is_confident():
    mapping = map_type(
        "RAW(16)",
        sample_values=["A1B2C3D4E5F60718293A4B5C6D7E8F90",
                       "0123456789ABCDEF0123456789ABCDEF"],
    )
    assert mapping.postgres_type == "uuid"
    assert mapping.confidence is Confidence.CONFIDENT


def test_raw16_without_samples_still_says_uuid_but_asks_to_check():
    """The DDL alone cannot distinguish a GUID from a 16-byte hash. The
    mapping guesses the common case and says it is guessing."""
    mapping = map_type("RAW(16)")
    assert mapping.postgres_type == "uuid"
    assert mapping.needs_review


def test_other_raw_lengths_are_bytea():
    assert map_type("RAW(2000)").postgres_type == "bytea"


@pytest.mark.parametrize(
    "oracle,expected",
    [
        ("CLOB", "text"),
        ("NCLOB", "text"),
        ("BLOB", "bytea"),
        ("BINARY_FLOAT", "real"),
        ("BINARY_DOUBLE", "double precision"),
        ("XMLTYPE", "xml"),
    ],
)
def test_lob_and_scalar_types(oracle, expected):
    assert map_type(oracle).postgres_type == expected


def test_rowid_is_never_silently_mapped():
    mapping = map_type("ROWID")
    assert mapping.confidence is Confidence.MANUAL
    assert "vacuum" in mapping.reason.lower()


def test_unknown_type_defaults_to_text_but_demands_review():
    mapping = map_type("SDO_GEOMETRY")
    assert mapping.confidence is Confidence.MANUAL
    assert "placeholder" in mapping.reason.lower()


# ------------------------------------------------------------- naming
def test_identifiers_are_lowercased_not_quoted():
    """Oracle folds unquoted names to upper, PostgreSQL to lower. Quoting
    to preserve the uppercase name would force every query afterwards to
    quote it too."""
    assert quote_policy("UCC_FILING") == "ucc_filing"
    assert '"' not in quote_policy("UCC_FILING")


# ------------------------------------- the actual columns in this lab
@pytest.mark.parametrize(
    "column,oracle,expected",
    [
        ("UCC_FILING.FILING_ID", "NUMBER(12)", "bigint"),
        ("UCC_FILING.FILED_DATE", "DATE", "timestamp(0)"),
        ("UCC_FILING.LAPSE_DATE", "DATE", "timestamp(0)"),
        ("UCC_FILING.COLLATERAL_DESC", "CLOB", "text"),
        ("UCC_FILING.PAGE_COUNT", "NUMBER(4,0)", "smallint"),
        ("UCC_FILING.FILING_FEE", "NUMBER(9,2)", "numeric(9,2)"),
        ("UCC_DEBTOR.MAILING_ADDRESS_2", "VARCHAR2(120 BYTE)", "varchar(120)"),
        ("UCC_SECURED_PARTY.TAX_ID", "RAW(16)", "uuid"),
        ("STATE_SOS_SOURCE.STATE_CODE", "CHAR(2)", "char(2)"),
        ("STATE_SOS_SOURCE.LAST_SYNC", "TIMESTAMP WITH LOCAL TIME ZONE", "timestamptz"),
        ("STATE_SOS_SOURCE.RECORDS_EXPECTED", "NUMBER", "numeric"),
        ("FILING_AUDIT.DOC_IMAGE", "BLOB", "bytea"),
        ("FILING_AUDIT.ACTION_TS", "TIMESTAMP(6)", "timestamp(6)"),
    ],
)
def test_every_column_in_the_legacy_schema(column, oracle, expected):
    assert map_type(oracle).postgres_type == expected, column
