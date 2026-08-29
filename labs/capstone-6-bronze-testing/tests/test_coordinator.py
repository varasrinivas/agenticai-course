"""
Tests for the Coordinator Agent

Validates manifest loading, Bronze table loading, single-state testing,
and parallel execution.
"""

import json
import os
import sys
import pytest

SOLUTION_DIR = os.path.join(os.path.dirname(__file__), "..", "solution")
STARTER_DIR = os.path.join(os.path.dirname(__file__), "..", "starter")
sys.path.insert(0, SOLUTION_DIR)

from coordinator import Coordinator

MOCK_DATA_DIR = os.path.join(STARTER_DIR, "mock_data")


class TestLoadManifest:
    """Test manifest loading."""

    def test_loads_manifest_successfully(self):
        coord = Coordinator(mock_data_dir=MOCK_DATA_DIR)
        coord.load_manifest()
        assert "states" in coord.manifest
        assert len(coord.manifest["states"]) == 16

    def test_manifest_states_have_required_fields(self):
        coord = Coordinator(mock_data_dir=MOCK_DATA_DIR)
        coord.load_manifest()
        for state_config in coord.manifest["states"]:
            assert "state" in state_config
            assert "source_file" in state_config
            assert "format" in state_config
            assert "expected_record_count" in state_config

    def test_raises_on_missing_manifest(self):
        coord = Coordinator(mock_data_dir="/nonexistent/path")
        with pytest.raises(FileNotFoundError):
            coord.load_manifest()


class TestLoadBronzeTable:
    """Test Bronze table loading."""

    def test_loads_bronze_table(self):
        coord = Coordinator(mock_data_dir=MOCK_DATA_DIR)
        coord.load_bronze_table()
        assert len(coord.bronze_records) > 0

    def test_bronze_records_have_state_field(self):
        coord = Coordinator(mock_data_dir=MOCK_DATA_DIR)
        coord.load_bronze_table()
        for record in coord.bronze_records:
            assert "state" in record


class TestGetBronzeRecordsForState:
    """Test state-level Bronze record filtering."""

    def test_filters_ny_records(self):
        coord = Coordinator(mock_data_dir=MOCK_DATA_DIR)
        coord.load_bronze_table()
        ny_records = coord.get_bronze_records_for_state("NY")
        assert len(ny_records) == 15
        for r in ny_records:
            assert r["state"] == "NY"

    def test_returns_empty_for_unknown_state(self):
        coord = Coordinator(mock_data_dir=MOCK_DATA_DIR)
        coord.load_bronze_table()
        records = coord.get_bronze_records_for_state("ZZ")
        assert records == []

    def test_no_tx_bad_in_bronze(self):
        """TX_BAD and FL_BAD should have no Bronze records."""
        coord = Coordinator(mock_data_dir=MOCK_DATA_DIR)
        coord.load_bronze_table()
        assert coord.get_bronze_records_for_state("TX_BAD") == []
        assert coord.get_bronze_records_for_state("FL_BAD") == []


class TestRunSingleState:
    """Test single-state validation."""

    def test_run_clean_state(self):
        coord = Coordinator(mock_data_dir=MOCK_DATA_DIR)
        coord.load_manifest()
        coord.load_bronze_table()

        # Find NY config
        ny_config = next(
            s for s in coord.manifest["states"] if s["state"] == "NY"
        )
        result = coord.run_state_test(ny_config)

        assert result["state"] == "NY"
        assert "summary" in result
        assert "checks" in result
        assert len(result["checks"]) == 12  # All 12 checks should run

    def test_run_error_state(self):
        """TX_BAD should have at least one FAIL."""
        coord = Coordinator(mock_data_dir=MOCK_DATA_DIR)
        coord.load_manifest()
        coord.load_bronze_table()

        tx_bad_config = next(
            s for s in coord.manifest["states"] if s["state"] == "TX_BAD"
        )
        result = coord.run_state_test(tx_bad_config)

        assert result["state"] == "TX_BAD"
        assert result["summary"]["fail"] > 0


class TestRunParallel:
    """Test parallel execution of all state tests."""

    def test_parallel_returns_all_states(self):
        coord = Coordinator(mock_data_dir=MOCK_DATA_DIR, max_workers=3)
        coord.load_manifest()
        coord.load_bronze_table()
        results = coord.run_parallel()

        assert len(results) == 16
        states_tested = {r["state"] for r in results}
        expected_states = {s["state"] for s in coord.manifest["states"]}
        assert states_tested == expected_states

    def test_parallel_results_have_summaries(self):
        coord = Coordinator(mock_data_dir=MOCK_DATA_DIR, max_workers=3)
        coord.load_manifest()
        coord.load_bronze_table()
        results = coord.run_parallel()

        for result in results:
            assert "summary" in result
            assert "pass" in result["summary"]
            assert "fail" in result["summary"]
            assert "warn" in result["summary"]
