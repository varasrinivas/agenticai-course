"""
Coordinator Agent — SOLUTION

Orchestrates parallel state testing:
1. Reads load_manifest.json to discover states to validate
2. Loads the Bronze table
3. Spawns StateTester subagents for each state (in parallel)
4. Aggregates results into a unified report
5. Optionally uses Claude to analyze failures and recommend fixes
"""

import asyncio
import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from state_tester import StateTester
from dashboard import Dashboard

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


class Coordinator:
    """
    Main coordinator agent that orchestrates Bronze table validation.
    """

    def __init__(self, mock_data_dir: str = "mock_data", max_workers: int = 5):
        """
        Args:
            mock_data_dir: Path to the mock_data directory
            max_workers: Maximum parallel state testers
        """
        self.mock_data_dir = mock_data_dir
        self.max_workers = max_workers
        self.manifest: dict = {}
        self.bronze_records: list[dict] = []
        self.results: list[dict] = []

    def load_manifest(self) -> None:
        """Load the load_manifest.json file."""
        manifest_path = Path(self.mock_data_dir) / "load_manifest.json"
        with open(manifest_path) as f:
            self.manifest = json.load(f)
        logger.info(
            f"Loaded manifest: {len(self.manifest.get('states', []))} states to validate"
        )

    def load_bronze_table(self) -> None:
        """Load the bronze_table.json file."""
        bronze_path = Path(self.mock_data_dir) / "bronze_table.json"
        with open(bronze_path) as f:
            data = json.load(f)
            self.bronze_records = data.get("records", [])
        logger.info(f"Loaded Bronze table: {len(self.bronze_records)} records")

    def get_bronze_records_for_state(self, state: str) -> list[dict]:
        """Filter Bronze records for a specific state."""
        return [r for r in self.bronze_records if r.get("state") == state]

    def run_state_test(self, state_config: dict) -> dict[str, Any]:
        """
        Run validation for a single state.

        Args:
            state_config: Dict from manifest with state, source_file, format, etc.

        Returns:
            StateTester result dict
        """
        state = state_config["state"]
        source_file = state_config["source_file"]
        file_format = state_config["format"]
        expected_count = state_config.get("expected_record_count", 0)
        bronze_recs = self.get_bronze_records_for_state(state)

        tester = StateTester(
            state=state,
            source_file=source_file,
            file_format=file_format,
            bronze_records=bronze_recs,
            expected_count=expected_count,
            mock_data_dir=self.mock_data_dir,
        )
        return tester.run()

    def run_parallel(self) -> list[dict[str, Any]]:
        """
        Run all state tests in parallel using ThreadPoolExecutor.

        Returns:
            List of result dicts, one per state
        """
        states = self.manifest.get("states", [])
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_state = {
                executor.submit(self.run_state_test, sc): sc["state"]
                for sc in states
            }
            for future in as_completed(future_to_state):
                state = future_to_state[future]
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(
                        f"[{state}] Completed: "
                        f"{result['summary']['pass']}P / "
                        f"{result['summary']['fail']}F / "
                        f"{result['summary']['warn']}W"
                    )
                except Exception as e:
                    logger.error(f"[{state}] Error: {e}")
                    results.append({
                        "state": state,
                        "source_file": "",
                        "checks": [],
                        "summary": {"pass": 0, "fail": 1, "warn": 0},
                        "error": str(e),
                    })

        self.results = results
        return results

    def run(self) -> None:
        """Main entry point — load data, run tests, generate dashboard."""
        self.load_manifest()
        self.load_bronze_table()
        results = self.run_parallel()

        dashboard = Dashboard(results)
        dashboard.print_console()
        dashboard.generate_html("validation_report.html")
        dashboard.generate_json("validation_report.json")

        # Exit with non-zero if any failures
        total_fails = sum(r["summary"]["fail"] for r in results)
        if total_fails > 0:
            logger.warning(f"Validation completed with {total_fails} total failures")
            sys.exit(1)
        else:
            logger.info("All validations passed!")


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Bronze Table Validation Coordinator")
    parser.add_argument(
        "--data-dir",
        default="mock_data",
        help="Path to mock_data directory (default: mock_data)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=5,
        help="Max parallel workers (default: 5)",
    )
    parser.add_argument(
        "--html-output",
        default="validation_report.html",
        help="Path for HTML report output",
    )
    parser.add_argument(
        "--json-output",
        default="validation_report.json",
        help="Path for JSON report output",
    )
    args = parser.parse_args()

    coordinator = Coordinator(mock_data_dir=args.data_dir, max_workers=args.workers)
    coordinator.run()


if __name__ == "__main__":
    main()
