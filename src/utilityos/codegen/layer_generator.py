"""Generate bronze/silver/gold layer schemas."""

from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Column,
    Identity,
    MetaData,
    String,
    Table,
    Text,
)
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID

from utilityos.codegen.ddl_generator import generate_table
from utilityos.models.schema import CommonDefinitions, EntityDefinition


def generate_bronze_table(
    entity_def: EntityDefinition,
    metadata: MetaData,
    source_system: str = "unknown",
) -> Table:
    """Generate a bronze-layer staging table.

    Bronze tables have all TEXT columns (no type enforcement)
    plus metadata columns for lineage tracking.
    """
    entity_name = entity_def.entity.name
    table_name = f"{source_system}_{entity_name}"

    # All business keys and attributes as TEXT
    columns: list[Column] = []  # type: ignore[type-arg]

    # Row ID
    columns.append(
        Column(
            "_row_id",
            BigInteger(),
            Identity(always=True),
            primary_key=True,
        )
    )

    # Business key columns as TEXT
    for bk in entity_def.keys.business:
        columns.append(Column(bk.name, Text()))

    # All attributes as TEXT
    for attr in entity_def.attributes:
        columns.append(Column(attr.name, Text()))

    # Bronze metadata columns
    columns.extend([
        Column("_batch_id", UUID(), nullable=False),
        Column("_ingested_at", TIMESTAMP(timezone=True), nullable=False),
        Column("_source_system", String(100), nullable=False),
        Column("_source_file", String(500)),
        Column("_row_number", BigInteger()),
    ])

    return Table(
        table_name,
        metadata,
        *columns,
        comment=f"Bronze staging table for {entity_name} from {source_system}",
    )


def generate_silver_table(
    entity_def: EntityDefinition,
    metadata: MetaData,
    common: CommonDefinitions | None = None,
) -> Table:
    """Generate a silver-layer canonical table.

    This is the conformed table matching the canonical model exactly.
    Delegates to the core DDL generator.
    """
    return generate_table(entity_def, metadata, common)


def generate_gold_dimension_table(
    entity_def: EntityDefinition,
    metadata: MetaData,
    common: CommonDefinitions | None = None,
) -> Table | None:
    """Generate a gold-layer dimension table.

    Returns None if the entity is not configured as a dimension.
    """
    if entity_def.gold_layer is None or not entity_def.gold_layer.dimension:
        return None

    # For SCD2 dimensions, the gold table mirrors silver structure
    # with a dim_ prefix
    gold_metadata = MetaData(schema=metadata.schema)

    # Reuse the silver table structure but with dim_ prefix
    silver_table = generate_table(entity_def, gold_metadata, common)

    # Create a new table with dim_ prefix
    dim_columns = [col.copy() for col in silver_table.columns]
    return Table(
        f"dim_{entity_def.entity.name}",
        metadata,
        *dim_columns,
        comment=f"Gold dimension table for {entity_def.entity.display_name}",
    )


def generate_gold_fact_table(
    entity_def: EntityDefinition,
    metadata: MetaData,
    common: CommonDefinitions | None = None,
) -> Table | None:
    """Generate a gold-layer fact table.

    Returns None if the entity is not configured as a fact.
    """
    if entity_def.gold_layer is None or not entity_def.gold_layer.fact:
        return None

    # Fact tables mirror the silver structure with fact_ prefix
    gold_metadata = MetaData(schema=metadata.schema)
    silver_table = generate_table(entity_def, gold_metadata, common)

    fact_columns = [col.copy() for col in silver_table.columns]
    return Table(
        f"fact_{entity_def.entity.name}",
        metadata,
        *fact_columns,
        comment=f"Gold fact table for {entity_def.entity.display_name}",
    )
