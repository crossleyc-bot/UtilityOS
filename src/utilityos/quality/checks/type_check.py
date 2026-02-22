"""Data type validation check."""

from __future__ import annotations

from utilityos.common.types import QualityCheckStatus
from utilityos.quality.schema import QualityCheckResult


def check_data_type(
    entity_name: str,
    column_name: str,
    expected_type: str,
    layer: str = "silver",
    total_rows: int = 0,
    invalid_count: int = 0,
) -> QualityCheckResult:
    """Check that column values conform to expected data type."""
    failed = invalid_count > 0
    failure_rate = invalid_count / total_rows if total_rows > 0 else 0.0

    return QualityCheckResult(
        check_type="data_type",
        check_name=f"{entity_name}.{column_name}_type_{expected_type}",
        entity_name=entity_name,
        layer=layer,
        status=QualityCheckStatus.FAILED if failed else QualityCheckStatus.PASSED,
        records_checked=total_rows,
        records_failed=invalid_count,
        failure_rate=failure_rate,
        message=(
            f"Column '{column_name}' has {invalid_count} values "
            f"that don't match expected type '{expected_type}'"
            if failed
            else f"Column '{column_name}' type validation passed"
        ),
    )
