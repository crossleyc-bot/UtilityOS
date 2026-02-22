"""Bridge between UtilityOS model definitions and Alembic migrations."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import MetaData

from utilityos.codegen.ddl_generator import generate_all_tables
from utilityos.models.loader import load_all_entities, load_common_definitions


def build_target_metadata(
    schema: str = "silver",
    definitions_dir: Path | None = None,
) -> MetaData:
    """Build the full SQLAlchemy MetaData from all YAML definitions.

    This is the 'target' state that Alembic compares against
    the live database to generate migration scripts.
    """
    common = load_common_definitions(definitions_dir)
    entities = load_all_entities(definitions_dir)
    metadata = MetaData(schema=schema)
    generate_all_tables(entities, metadata, common)
    return metadata
