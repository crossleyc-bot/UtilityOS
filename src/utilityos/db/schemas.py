"""PostgreSQL schema management for data layers."""

from __future__ import annotations

from sqlalchemy import Engine, text

from utilityos.common.types import DataLayer

LAYER_SCHEMAS = [
    DataLayer.BRONZE,
    DataLayer.SILVER,
    DataLayer.GOLD,
    DataLayer.META,
]


def create_schemas(engine: Engine) -> list[str]:
    """Create all data layer schemas in PostgreSQL.

    Returns the list of schema names created.
    """
    created = []
    with engine.begin() as conn:
        for layer in LAYER_SCHEMAS:
            schema_name = layer.value
            conn.execute(
                text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
            )
            created.append(schema_name)
    return created


def drop_schemas(engine: Engine) -> list[str]:
    """Drop all data layer schemas (CASCADE). Use with caution.

    Returns the list of schema names dropped.
    """
    dropped = []
    with engine.begin() as conn:
        for layer in reversed(LAYER_SCHEMAS):
            schema_name = layer.value
            conn.execute(
                text(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE")
            )
            dropped.append(schema_name)
    return dropped


def list_schemas(engine: Engine) -> list[str]:
    """List all UtilityOS schemas that exist in the database."""
    existing = []
    with engine.connect() as conn:
        result = conn.execute(
            text(
                "SELECT schema_name FROM information_schema.schemata "
                "WHERE schema_name = ANY(:names)"
            ),
            {"names": [layer.value for layer in LAYER_SCHEMAS]},
        )
        existing = [row[0] for row in result]
    return existing
