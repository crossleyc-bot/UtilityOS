"""Schema drift detection check."""

from __future__ import annotations

from utilityos.common.types import QualityCheckStatus
from utilityos.quality.schema import QualityCheckResult


def check_schema_drift(
    entity_name: str,
    expected_columns: list[str],
    actual_columns: list[str],
    layer: str = "silver",
) -> QualityCheckResult:
    """Check that actual table columns match expected model definition."""
    expected_set = set(expected_columns)
    actual_set = set(actual_columns)

    missing = expected_set - actual_set
    extra = actual_set - expected_set

    failed = bool(missing or extra)

    details = {}
    if missing:
        details["missing_columns"] = sorted(missing)
    if extra:
        details["extra_columns"] = sorted(extra)

    return QualityCheckResult(
        check_type="schema_drift",
        check_name=f"{entity_name}_schema_drift",
        entity_name=entity_name,
        layer=layer,
        status=QualityCheckStatus.FAILED if failed else QualityCheckStatus.PASSED,
        records_checked=len(expected_columns),
        records_failed=len(missing) + len(extra),
        failure_rate=(len(missing) + len(extra)) / max(len(expected_columns), 1),
        message=(
            f"Schema drift detected: {len(missing)} missing, {len(extra)} extra columns"
            if failed
            else "Schema matches expected model definition"
        ),
        details=details if details else None,
    )


def generate_column_list_sql(
    entity_name: str,
    schema: str = "silver",
) -> str:
    """Generate SQL to list all columns in a table."""
    return (
        f"SELECT column_name FROM information_schema.columns "
        f"WHERE table_schema = '{schema}' AND table_name = '{entity_name}' "
        f"ORDER BY ordinal_position"
    )
