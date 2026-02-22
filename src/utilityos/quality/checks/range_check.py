"""Value range and reasonableness checks."""

from __future__ import annotations

from utilityos.common.types import QualityCheckStatus
from utilityos.quality.schema import QualityCheckResult


def check_range(
    entity_name: str,
    column_name: str,
    layer: str = "silver",
    total_rows: int = 0,
    out_of_range_count: int = 0,
    min_value: float | None = None,
    max_value: float | None = None,
) -> QualityCheckResult:
    """Check that numeric values fall within expected bounds."""
    failed = out_of_range_count > 0
    failure_rate = out_of_range_count / total_rows if total_rows > 0 else 0.0

    bounds = []
    if min_value is not None:
        bounds.append(f">= {min_value}")
    if max_value is not None:
        bounds.append(f"<= {max_value}")
    bounds_str = " and ".join(bounds) if bounds else "any"

    return QualityCheckResult(
        check_type="range",
        check_name=f"{entity_name}.{column_name}_range",
        entity_name=entity_name,
        layer=layer,
        status=QualityCheckStatus.FAILED if failed else QualityCheckStatus.PASSED,
        records_checked=total_rows,
        records_failed=out_of_range_count,
        failure_rate=failure_rate,
        message=(
            f"Column '{column_name}' has {out_of_range_count} values "
            f"outside expected range ({bounds_str})"
            if failed
            else f"Column '{column_name}' values are within range ({bounds_str})"
        ),
    )


def generate_range_check_sql(
    entity_name: str,
    column_name: str,
    schema: str = "silver",
    min_value: float | None = None,
    max_value: float | None = None,
) -> str:
    """Generate SQL to count values outside expected range."""
    conditions = []
    if min_value is not None:
        conditions.append(f"{column_name} < {min_value}")
    if max_value is not None:
        conditions.append(f"{column_name} > {max_value}")

    if not conditions:
        return (
            f"SELECT COUNT(*) AS total_rows, 0 AS out_of_range_count "
            f"FROM {schema}.{entity_name}"
        )

    filter_expr = " OR ".join(conditions)
    return (
        f"SELECT COUNT(*) AS total_rows, "
        f"COUNT(*) FILTER (WHERE {filter_expr}) AS out_of_range_count "
        f"FROM {schema}.{entity_name} "
        f"WHERE {column_name} IS NOT NULL"
    )
