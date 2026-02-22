"""Table partitioning logic for PostgreSQL."""

from __future__ import annotations

from utilityos.common.types import PartitionStrategy
from utilityos.models.schema import EntityDefinition


def generate_partition_clause(entity_def: EntityDefinition) -> str | None:
    """Generate a PARTITION BY clause for a table if partitioning is defined.

    Returns the SQL clause string or None if no partitioning.
    """
    if entity_def.partitioning is None:
        return None
    if entity_def.partitioning.strategy == PartitionStrategy.NONE:
        return None
    if entity_def.partitioning.column is None:
        return None

    strategy = entity_def.partitioning.strategy
    column = entity_def.partitioning.column

    if strategy == PartitionStrategy.RANGE:
        return f"PARTITION BY RANGE ({column})"
    elif strategy == PartitionStrategy.LIST:
        return f"PARTITION BY LIST ({column})"
    elif strategy == PartitionStrategy.HASH:
        return f"PARTITION BY HASH ({column})"

    return None
