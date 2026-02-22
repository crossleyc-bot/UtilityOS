"""Auto-generate index definitions from entity metadata."""

from __future__ import annotations

from sqlalchemy import Index, Table

from utilityos.common.types import SCDType
from utilityos.models.schema import EntityDefinition


def generate_indexes(
    entity_def: EntityDefinition,
    table: Table,
) -> list[Index]:
    """Generate all indexes for a table based on entity definition.

    Auto-generates:
    1. Unique index on business key (filtered for SCD2 current records)
    2. Indexes from explicit YAML definitions
    3. Composite SCD2 index on (business_key, effective_from)
    """
    indexes: list[Index] = []
    entity_name = entity_def.entity.name
    is_scd2 = entity_def.entity.scd_type == SCDType.TYPE2

    # 1. Business key unique index
    bk_columns = [bk.name for bk in entity_def.keys.business]
    if bk_columns:
        bk_cols = [table.c[col] for col in bk_columns if col in table.c]
        if bk_cols:
            kwargs: dict = {}
            if is_scd2 and "is_current" in table.c:
                kwargs["postgresql_where"] = table.c.is_current == True  # noqa: E712
            indexes.append(
                Index(
                    f"ix_{entity_name}_bk_{'_'.join(bk_columns)}",
                    *bk_cols,
                    unique=True,
                    **kwargs,
                )
            )

    # 2. SCD2 composite index: (business_key, effective_from)
    if is_scd2 and "effective_from" in table.c:
        scd_cols = [table.c[col] for col in bk_columns if col in table.c]
        scd_cols.append(table.c.effective_from)
        indexes.append(
            Index(
                f"ix_{entity_name}_scd2_{'_'.join(bk_columns)}_eff",
                *scd_cols,
            )
        )

    # 3. is_current partial index for SCD2
    if is_scd2 and "is_current" in table.c:
        indexes.append(
            Index(
                f"ix_{entity_name}_current",
                table.c.is_current,
                postgresql_where=table.c.is_current == True,  # noqa: E712
            )
        )

    # 4. Explicit YAML-defined indexes
    if entity_def.indexes:
        for i, idx_def in enumerate(entity_def.indexes):
            idx_cols = [
                table.c[col]
                for col in idx_def.columns
                if col in table.c
            ]
            if not idx_cols:
                continue
            kwargs = {}
            if idx_def.where and "is_current" in idx_def.where and "is_current" in table.c:
                kwargs["postgresql_where"] = table.c.is_current == True  # noqa: E712
            indexes.append(
                Index(
                    f"ix_{entity_name}_{'_'.join(idx_def.columns)}_{i}",
                    *idx_cols,
                    unique=idx_def.unique,
                    **kwargs,
                )
            )

    return indexes
