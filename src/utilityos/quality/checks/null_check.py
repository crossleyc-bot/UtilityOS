"""Null/not-null validation check."""

from __future__ import annotations

from utilityos.common.types import QualityCheckStatus
from utilityos.quality.schema import QualityCheckResult


def check_not_null(
    entity_name: str,
    column_name: str,
    layer: str = "silver",
    total_rows: int = 0,
    null_count: int = 0,
) -> QualityCheckResult:
    """Check that a column has no NULL values."""
    failed = null_count > 0
    failure_rate = null_count / total_rows if total_rows > 0 else 0.0

    return QualityCheckResult(
        check_type="not_null",
        check_name=f"{entity_name}.{column_name}_not_null",
        entity_name=entity_name,
        layer=layer,
        status=QualityCheckStatus.FAILED if failed else QualityCheckStatus.PASSED,
        records_checked=total_rows,
        records_failed=null_count,
        failure_rate=failure_rate,
        message=(
            f"Column '{column_name}' has {null_count} NULL values"
            if failed
            else f"Column '{column_name}' has no NULL values"
        ),
    )


def generate_null_check_sql(
    entity_name: str,
    column_name: str,
    schema: str = "silver",
) -> str:
    """Generate SQL to count NULL values in a column."""
    return (
        f"SELECT COUNT(*) AS total_rows, "
        f"COUNT(*) FILTER (WHERE {column_name} IS NULL) AS null_count "
        f"FROM {schema}.{entity_name}"
    )
