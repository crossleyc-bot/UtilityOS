"""Data quality check orchestration engine."""

from __future__ import annotations

from utilityos.common.types import QualityCheckStatus
from utilityos.models.registry import ModelRegistry
from utilityos.models.schema import EntityDefinition
from utilityos.quality.checks.null_check import check_not_null
from utilityos.quality.checks.uniqueness_check import check_uniqueness
from utilityos.quality.schema import QualityCheckResult, QualityReport


class QualityEngine:
    """Orchestrates data quality checks for entities."""

    def __init__(self, registry: ModelRegistry):
        self.registry = registry

    def derive_checks_for_entity(
        self,
        entity_name: str,
        layer: str = "silver",
    ) -> list[dict]:
        """Derive quality check specifications from entity definition.

        Returns a list of check specifications that can be executed
        against a database or used for validation.
        """
        entity_def = self.registry.get(entity_name)
        checks: list[dict] = []

        # Auto-derive not-null checks from non-nullable attributes
        for attr in entity_def.attributes:
            if not attr.nullable:
                checks.append({
                    "type": "not_null",
                    "entity": entity_name,
                    "column": attr.name,
                    "layer": layer,
                })

        # Business key uniqueness
        bk_columns = [bk.name for bk in entity_def.keys.business]
        if bk_columns:
            checks.append({
                "type": "uniqueness",
                "entity": entity_name,
                "columns": bk_columns,
                "layer": layer,
                "scope": "current_records" if entity_def.entity.scd_type.value == 2 else None,
            })

        # Enum validation checks
        for attr in entity_def.attributes:
            if attr.enum_ref:
                checks.append({
                    "type": "enum_valid",
                    "entity": entity_name,
                    "column": attr.name,
                    "enum_ref": attr.enum_ref,
                    "layer": layer,
                })

        # Explicit quality rules from YAML
        if entity_def.quality_rules:
            for rule in entity_def.quality_rules:
                checks.append({
                    "type": rule.rule,
                    "entity": entity_name,
                    "columns": rule.columns,
                    "column": rule.column,
                    "layer": layer,
                    "enum_ref": rule.enum_ref,
                    "condition": rule.condition,
                    "scope": rule.scope,
                    "message": rule.message,
                })

        return checks

    def validate_in_memory(
        self,
        entity_name: str,
        rows: list[dict],
        layer: str = "silver",
    ) -> QualityReport:
        """Run quality checks against in-memory data (no DB required).

        Useful for validating pipeline data before loading.
        """
        entity_def = self.registry.get(entity_name)
        results: list[QualityCheckResult] = []

        # Not-null checks
        for attr in entity_def.attributes:
            if not attr.nullable:
                null_count = sum(
                    1 for row in rows if row.get(attr.name) is None
                )
                results.append(
                    check_not_null(
                        entity_name=entity_name,
                        column_name=attr.name,
                        layer=layer,
                        total_rows=len(rows),
                        null_count=null_count,
                    )
                )

        # Business key uniqueness
        bk_columns = [bk.name for bk in entity_def.keys.business]
        if bk_columns:
            seen_keys: set = set()
            dup_count = 0
            for row in rows:
                key = tuple(row.get(col) for col in bk_columns)
                if key in seen_keys:
                    dup_count += 1
                seen_keys.add(key)

            results.append(
                check_uniqueness(
                    entity_name=entity_name,
                    columns=bk_columns,
                    layer=layer,
                    total_rows=len(rows),
                    duplicate_count=dup_count,
                )
            )

        # Enum validation
        for attr in entity_def.attributes:
            if attr.enum_ref:
                try:
                    valid_values = self.registry.get_enum_values(attr.enum_ref)
                    invalid_count = sum(
                        1
                        for row in rows
                        if row.get(attr.name) is not None
                        and row.get(attr.name) not in valid_values
                    )
                    results.append(
                        QualityCheckResult(
                            check_type="enum_valid",
                            check_name=f"{entity_name}.{attr.name}_enum_{attr.enum_ref}",
                            entity_name=entity_name,
                            layer=layer,
                            status=(
                                QualityCheckStatus.FAILED
                                if invalid_count > 0
                                else QualityCheckStatus.PASSED
                            ),
                            records_checked=len(rows),
                            records_failed=invalid_count,
                            failure_rate=(
                                invalid_count / len(rows) if rows else 0.0
                            ),
                            message=(
                                f"Column '{attr.name}' has {invalid_count} "
                                f"values not in enum '{attr.enum_ref}'"
                                if invalid_count > 0
                                else f"Column '{attr.name}' enum validation passed"
                            ),
                        )
                    )
                except Exception:
                    pass

        return QualityReport(
            entity_name=entity_name,
            layer=layer,
            results=results,
        )
