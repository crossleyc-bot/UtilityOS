"""Uniqueness and duplicate detection check."""

from __future__ import annotations

from utilityos.common.types import QualityCheckStatus
from utilityos.quality.schema import QualityCheckResult


def check_uniqueness(
    entity_name: str,
    columns: list[str],
    layer: str = "silver",
    total_rows: int = 0,
    duplicate_count: int = 0,
    scope: str | None = None,
) -> QualityCheckResult:
    """Check that columns are unique (optionally scoped to current records)."""
    failed = duplicate_count > 0
    col_str = ", ".join(columns)
    failure_rate = duplicate_count / total_rows if total_rows > 0 else 0.0

    return QualityCheckResult(
        check_type="uniqueness",
        check_name=f"{entity_name}.{'_'.join(columns)}_unique",
        entity_name=entity_name,
        layer=layer,
        status=QualityCheckStatus.FAILED if failed else QualityCheckStatus.PASSED,
        records_checked=total_rows,
        records_failed=duplicate_count,
        failure_rate=failure_rate,
        message=(
            f"Columns ({col_str}) have {duplicate_count} duplicate values"
            if failed
            else f"Columns ({col_str}) are unique"
        ),
    )


def generate_uniqueness_check_sql(
    entity_name: str,
    columns: list[str],
    schema: str = "silver",
    scope: str | None = None,
) -> str:
    """Generate SQL to detect duplicates on specified columns."""
    col_str = ", ".join(columns)
    where_clause = ""
    if scope == "current_records":
        where_clause = "WHERE is_current = TRUE"

    return (
        f"SELECT COUNT(*) AS total_rows, "
        f"COUNT(*) - COUNT(DISTINCT ({col_str})) AS duplicate_count "
        f"FROM {schema}.{entity_name} {where_clause}"
    )
