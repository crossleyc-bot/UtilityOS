"""Referential integrity check."""

from __future__ import annotations

from utilityos.common.types import QualityCheckStatus
from utilityos.quality.schema import QualityCheckResult


def check_referential_integrity(
    entity_name: str,
    fk_column: str,
    target_entity: str,
    target_column: str,
    layer: str = "silver",
    total_rows: int = 0,
    orphan_count: int = 0,
) -> QualityCheckResult:
    """Check that foreign key values exist in the target table."""
    failed = orphan_count > 0
    failure_rate = orphan_count / total_rows if total_rows > 0 else 0.0

    return QualityCheckResult(
        check_type="referential_integrity",
        check_name=f"{entity_name}.{fk_column}_ref_{target_entity}",
        entity_name=entity_name,
        layer=layer,
        status=QualityCheckStatus.FAILED if failed else QualityCheckStatus.PASSED,
        records_checked=total_rows,
        records_failed=orphan_count,
        failure_rate=failure_rate,
        message=(
            f"Column '{fk_column}' has {orphan_count} orphaned references "
            f"to {target_entity}.{target_column}"
            if failed
            else f"Column '{fk_column}' referential integrity is valid"
        ),
    )


def generate_referential_check_sql(
    entity_name: str,
    fk_column: str,
    target_entity: str,
    target_column: str,
    schema: str = "silver",
) -> str:
    """Generate SQL to detect orphaned foreign key references."""
    return (
        f"SELECT COUNT(*) AS total_rows, "
        f"COUNT(*) FILTER (WHERE t.{target_column} IS NULL) AS orphan_count "
        f"FROM {schema}.{entity_name} s "
        f"LEFT JOIN {schema}.{target_entity} t "
        f"ON s.{fk_column} = t.{target_column} "
        f"WHERE s.{fk_column} IS NOT NULL"
    )
