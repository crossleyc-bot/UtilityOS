"""Row count and sum reconciliation checks between layers."""

from __future__ import annotations

from utilityos.common.types import QualityCheckStatus
from utilityos.quality.schema import QualityCheckResult


def check_row_count_reconciliation(
    entity_name: str,
    source_layer: str,
    target_layer: str,
    source_count: int,
    target_count: int,
    tolerance: float = 0.0,
) -> QualityCheckResult:
    """Check that row counts match between layers within tolerance."""
    if source_count == 0:
        diff_pct = 0.0 if target_count == 0 else 1.0
    else:
        diff_pct = abs(source_count - target_count) / source_count

    failed = diff_pct > tolerance

    return QualityCheckResult(
        check_type="reconciliation_row_count",
        check_name=f"{entity_name}_{source_layer}_to_{target_layer}_count",
        entity_name=entity_name,
        layer=target_layer,
        status=QualityCheckStatus.FAILED if failed else QualityCheckStatus.PASSED,
        records_checked=source_count,
        records_failed=abs(source_count - target_count),
        failure_rate=diff_pct,
        message=(
            f"Row count mismatch: {source_layer}={source_count}, "
            f"{target_layer}={target_count} (diff={diff_pct:.1%})"
            if failed
            else f"Row counts match: {source_count} rows"
        ),
    )


def generate_row_count_sql(
    entity_name: str,
    schema: str,
) -> str:
    """Generate SQL to count rows in a table."""
    return f"SELECT COUNT(*) AS row_count FROM {schema}.{entity_name}"
