"""SCD Type 1/2 column generation and current-state view generation."""

from __future__ import annotations

from utilityos.common.types import SCDType
from utilityos.models.schema import EntityDefinition


def generate_current_view_sql(
    entity_def: EntityDefinition,
    schema: str = "silver",
) -> str | None:
    """Generate a CREATE VIEW statement for the current-state view of an SCD2 entity.

    Returns SQL string or None if entity is not SCD2.
    """
    if entity_def.entity.scd_type != SCDType.TYPE2:
        return None

    entity_name = entity_def.entity.name
    view_name = f"{entity_name}_current"
    table_ref = f"{schema}.{entity_name}"

    return (
        f"CREATE OR REPLACE VIEW {schema}.{view_name} AS\n"
        f"SELECT *\n"
        f"FROM {table_ref}\n"
        f"WHERE is_current = TRUE;"
    )


def generate_scd2_merge_sql(
    entity_def: EntityDefinition,
    schema: str = "silver",
    staging_schema: str = "bronze",
) -> str | None:
    """Generate a template MERGE/upsert SQL for SCD2 processing.

    Returns a SQL template string or None if not SCD2.
    This is a reference template — actual execution uses Python logic.
    """
    if entity_def.entity.scd_type != SCDType.TYPE2:
        return None

    entity_name = entity_def.entity.name
    bk_columns = [bk.name for bk in entity_def.keys.business]
    bk_join = " AND ".join(
        f"t.{col} = s.{col}" for col in bk_columns
    )

    attr_columns = [attr.name for attr in entity_def.attributes]
    change_detection = " OR ".join(
        f"t.{col} IS DISTINCT FROM s.{col}" for col in attr_columns
    )

    return f"""\
-- SCD Type 2 merge template for {entity_name}
-- Step 1: Close changed records
UPDATE {schema}.{entity_name} t
SET effective_to = CURRENT_TIMESTAMP,
    is_current = FALSE,
    updated_at = CURRENT_TIMESTAMP
FROM staging s
WHERE {bk_join}
  AND t.is_current = TRUE
  AND ({change_detection});

-- Step 2: Insert new/changed records
INSERT INTO {schema}.{entity_name} ({', '.join(bk_columns + attr_columns)},
    effective_from, effective_to, is_current, version_number,
    source_system, batch_id, created_at, updated_at)
SELECT {', '.join(f's.{col}' for col in bk_columns + attr_columns)},
    CURRENT_TIMESTAMP, NULL, TRUE,
    COALESCE(t.version_number, 0) + 1,
    s.source_system, s.batch_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
FROM staging s
LEFT JOIN {schema}.{entity_name} t
    ON {bk_join} AND t.is_current = TRUE
WHERE t.{entity_def.keys.surrogate.name} IS NULL
   OR ({change_detection});"""
