"""
Validation Results Dashboard — SOLUTION

Generates console output, HTML report, and JSON report from validation results.
"""

import json
from datetime import datetime
from typing import Any


class Dashboard:
    """
    Generates validation result dashboards in console, HTML, and JSON formats.
    """

    def __init__(self, results: list[dict[str, Any]]):
        """
        Args:
            results: List of state validation result dicts from coordinator
        """
        self.results = sorted(results, key=lambda r: r["state"])
        self.timestamp = datetime.now().isoformat()

    def get_summary(self) -> dict[str, Any]:
        """Calculate overall summary statistics."""
        total_pass = sum(r["summary"]["pass"] for r in self.results)
        total_fail = sum(r["summary"]["fail"] for r in self.results)
        total_warn = sum(r["summary"]["warn"] for r in self.results)
        states_clean = sum(
            1 for r in self.results if r["summary"]["fail"] == 0
        )
        states_with_errors = sum(
            1 for r in self.results if r["summary"]["fail"] > 0
        )

        return {
            "total_states": len(self.results),
            "states_clean": states_clean,
            "states_with_errors": states_with_errors,
            "total_pass": total_pass,
            "total_fail": total_fail,
            "total_warn": total_warn,
        }

    def print_console(self) -> str:
        """
        Print results to console in a formatted table.

        Returns:
            The formatted string (also printed to stdout)
        """
        summary = self.get_summary()

        output = []
        output.append("=" * 70)
        output.append("BRONZE TABLE VALIDATION REPORT")
        output.append(f"Timestamp: {self.timestamp}")
        output.append(f"Batch: {len(self.results)} states validated")
        output.append("=" * 70)
        output.append("")
        output.append(f"{'STATE':<10} {'PASS':>6} {'FAIL':>6} {'WARN':>6}  STATUS")
        output.append("-" * 70)

        for result in self.results:
            s = result["summary"]
            if s["fail"] > 0:
                status = "ERRORS"
            elif s["warn"] > 0:
                status = "WARNINGS"
            else:
                status = "CLEAN"
            output.append(
                f"{result['state']:<10} {s['pass']:>6} {s['fail']:>6} {s['warn']:>6}  {status}"
            )

        output.append("-" * 70)
        output.append(
            f"{'TOTAL':<10} {summary['total_pass']:>6} "
            f"{summary['total_fail']:>6} {summary['total_warn']:>6}"
        )
        output.append("")
        output.append(
            f"States clean: {summary['states_clean']} / {summary['total_states']}"
        )
        output.append(
            f"States with errors: {summary['states_with_errors']} / {summary['total_states']}"
        )

        # Failure details section
        failures_found = False
        for result in self.results:
            failed_checks = [c for c in result["checks"] if c["status"] == "FAIL"]
            if failed_checks:
                if not failures_found:
                    output.append("")
                    output.append("=" * 70)
                    output.append("FAILURE DETAILS")
                    output.append("=" * 70)
                    failures_found = True
                output.append("")
                output.append(f"--- {result['state']} ({result['source_file']}) ---")
                for check in failed_checks:
                    output.append(
                        f"  [{check['check_id']}] {check['check_name']}: {check['message']}"
                    )

        # Warning details section
        warnings_found = False
        for result in self.results:
            warn_checks = [c for c in result["checks"] if c["status"] == "WARN"]
            if warn_checks:
                if not warnings_found:
                    output.append("")
                    output.append("=" * 70)
                    output.append("WARNING DETAILS")
                    output.append("=" * 70)
                    warnings_found = True
                output.append("")
                output.append(f"--- {result['state']} ({result['source_file']}) ---")
                for check in warn_checks:
                    output.append(
                        f"  [{check['check_id']}] {check['check_name']}: {check['message']}"
                    )

        output.append("")
        output.append("=" * 70)

        text = "\n".join(output)
        print(text)
        return text

    def generate_html(self, output_path: str = "validation_report.html") -> str:
        """
        Generate an HTML validation report.

        Args:
            output_path: Path to write the HTML file

        Returns:
            Path to the generated HTML file
        """
        summary = self.get_summary()

        # Build per-state rows
        rows_html = ""
        for result in self.results:
            s = result["summary"]
            if s["fail"] > 0:
                row_class = "fail"
                status_text = "ERRORS"
            elif s["warn"] > 0:
                row_class = "warn"
                status_text = "WARNINGS"
            else:
                row_class = "pass"
                status_text = "CLEAN"
            rows_html += f"""
            <tr class="{row_class}">
                <td>{result['state']}</td>
                <td>{result['source_file']}</td>
                <td>{s['pass']}</td>
                <td>{s['fail']}</td>
                <td>{s['warn']}</td>
                <td>{status_text}</td>
            </tr>"""

        # Build failure detail sections
        details_html = ""
        for result in self.results:
            failed = [c for c in result["checks"] if c["status"] in ("FAIL", "WARN")]
            if failed:
                details_html += f"<h3>{result['state']} ({result['source_file']})</h3>"
                details_html += "<ul>"
                for check in failed:
                    badge = "fail-badge" if check["status"] == "FAIL" else "warn-badge"
                    details_html += (
                        f'<li><span class="{badge}">{check["status"]}</span> '
                        f'<strong>[{check["check_id"]}] {check["check_name"]}</strong>: '
                        f'{check["message"]}</li>'
                    )
                details_html += "</ul>"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bronze Table Validation Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 2em; background: #f8f9fa; color: #333; }}
        h1 {{ color: #1a1a2e; margin-bottom: 0.5em; }}
        .timestamp {{ color: #666; margin-bottom: 2em; font-size: 0.9em; }}
        .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1em; margin-bottom: 2em; }}
        .summary-card {{ background: white; border-radius: 8px; padding: 1.5em; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .summary-card .number {{ font-size: 2em; font-weight: bold; }}
        .summary-card .label {{ font-size: 0.85em; color: #666; margin-top: 0.3em; }}
        .card-pass .number {{ color: #28a745; }}
        .card-fail .number {{ color: #dc3545; }}
        .card-warn .number {{ color: #ffc107; }}
        table {{ border-collapse: collapse; width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 2em; }}
        th {{ background: #1a1a2e; color: white; padding: 12px 16px; text-align: left; font-weight: 600; }}
        td {{ border-bottom: 1px solid #eee; padding: 10px 16px; }}
        tr.pass {{ background: #d4edda; }}
        tr.fail {{ background: #f8d7da; }}
        tr.warn {{ background: #fff3cd; }}
        .details {{ background: white; border-radius: 8px; padding: 1.5em; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .details h2 {{ margin-bottom: 1em; color: #1a1a2e; }}
        .details h3 {{ margin-top: 1em; margin-bottom: 0.5em; color: #444; }}
        .details ul {{ margin-left: 1.5em; }}
        .details li {{ margin-bottom: 0.4em; line-height: 1.5; }}
        .fail-badge {{ background: #dc3545; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }}
        .warn-badge {{ background: #ffc107; color: #333; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>Bronze Table Validation Report</h1>
    <div class="timestamp">Generated: {self.timestamp}</div>

    <div class="summary-grid">
        <div class="summary-card">
            <div class="number">{summary['total_states']}</div>
            <div class="label">States Tested</div>
        </div>
        <div class="summary-card card-pass">
            <div class="number">{summary['states_clean']}</div>
            <div class="label">States Clean</div>
        </div>
        <div class="summary-card card-fail">
            <div class="number">{summary['states_with_errors']}</div>
            <div class="label">States with Errors</div>
        </div>
        <div class="summary-card card-pass">
            <div class="number">{summary['total_pass']}</div>
            <div class="label">Checks Passed</div>
        </div>
        <div class="summary-card card-fail">
            <div class="number">{summary['total_fail']}</div>
            <div class="label">Checks Failed</div>
        </div>
        <div class="summary-card card-warn">
            <div class="number">{summary['total_warn']}</div>
            <div class="label">Warnings</div>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>State</th>
                <th>Source File</th>
                <th>Pass</th>
                <th>Fail</th>
                <th>Warn</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>

    <div class="details">
        <h2>Issue Details</h2>
        {details_html if details_html else "<p>No issues found. All checks passed.</p>"}
    </div>
</body>
</html>"""

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"HTML report written to: {output_path}")
        return output_path

    def generate_json(self, output_path: str = "validation_report.json") -> str:
        """
        Generate a JSON validation report.

        Args:
            output_path: Path to write the JSON file

        Returns:
            Path to the generated JSON file
        """
        summary = self.get_summary()

        report = {
            "report_type": "bronze_table_validation",
            "timestamp": self.timestamp,
            "summary": summary,
            "states": [],
        }

        for result in self.results:
            state_entry = {
                "state": result["state"],
                "source_file": result["source_file"],
                "summary": result["summary"],
                "checks": result["checks"],
            }
            if "error" in result:
                state_entry["error"] = result["error"]
            report["states"].append(state_entry)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, default=str)
        print(f"JSON report written to: {output_path}")
        return output_path
