"""Quality check result persistence."""

from __future__ import annotations

from uuid import UUID

from utilityos.quality.schema import QualityCheckResult, QualityReport


def format_report_summary(report: QualityReport) -> str:
    """Format a quality report as a human-readable summary string."""
    lines = [
        f"Quality Report: {report.entity_name or 'All Entities'} "
        f"({report.layer} layer)",
        f"{'=' * 60}",
        f"Total Checks: {report.total_checks}",
        f"Passed:       {report.passed_checks}",
        f"Failed:       {report.failed_checks}",
        f"Pass Rate:    {report.pass_rate:.1%}",
        "",
    ]

    if report.results:
        lines.append(f"{'Check Name':<45} {'Status':<10} {'Failed':<10}")
        lines.append(f"{'-' * 45} {'-' * 10} {'-' * 10}")
        for r in report.results:
            status_str = "PASS" if r.passed else "FAIL"
            lines.append(
                f"{r.check_name:<45} {status_str:<10} {r.records_failed:<10}"
            )

    return "\n".join(lines)
