"""Generate SQLAlchemy Table objects and DDL from entity definitions."""

from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    Identity,
    Integer,
    MetaData,
    Numeric,
    SmallInteger,
    String,
    Table,
    Text,
    Uuid,
)
from sqlalchemy.dialects.postgresql import INTERVAL, JSONB, TIMESTAMP

from utilityos.common.exceptions import DDLGenerationError
from utilityos.common.types import DataType, SCDType
from utilityos.models.schema import (
    AttributeDefinition,
    CommonColumnDefinition,
    CommonDefinitions,
    EntityDefinition,
    KeyDefinition,
)

# Mapping from canonical DataType enum to SQLAlchemy column types
_TYPE_MAP = {
    DataType.VARCHAR: lambda attr: String(attr.length or 255),
    DataType.TEXT: lambda _: Text(),
    DataType.INTEGER: lambda _: Integer(),
    DataType.BIGINT: lambda _: BigInteger(),
    DataType.SMALLINT: lambda _: SmallInteger(),
    DataType.NUMERIC: lambda attr: Numeric(
        precision=attr.precision or 18, scale=attr.scale or 2
    ),
    DataType.BOOLEAN: lambda _: Boolean(),
    DataType.DATE: lambda _: Date(),
    DataType.TIMESTAMP: lambda _: TIMESTAMP(),
    DataType.TIMESTAMP_TZ: lambda _: TIMESTAMP(timezone=True),
    DataType.UUID: lambda _: Uuid(),
    DataType.JSONB: lambda _: JSONB(),
    DataType.INTERVAL: lambda _: INTERVAL(),
}


class _TypeProxy:
    """Proxy to pass length/precision/scale to type factory."""

    def __init__(
        self,
        length: int | None = None,
        precision: int | None = None,
        scale: int | None = None,
    ):
        self.length = length
        self.precision = precision
        self.scale = scale


def _resolve_column_type(data_type: DataType, attr: _TypeProxy | AttributeDefinition | KeyDefinition | CommonColumnDefinition):  # noqa: E501
    """Resolve a DataType enum to a SQLAlchemy column type."""
    factory = _TYPE_MAP.get(data_type)
    if factory is None:
        raise DDLGenerationError(f"Unsupported data type: {data_type}")
    return factory(attr)


def _build_surrogate_key_column(entity_def: EntityDefinition) -> Column:  # type: ignore[type-arg]
    """Build the surrogate key column."""
    sk = entity_def.keys.surrogate
    col_type = _resolve_column_type(sk.data_type, sk)
    return Column(
        sk.name,
        col_type,
        Identity(always=True),
        primary_key=True,
        comment=sk.description or f"Surrogate key for {entity_def.entity.name}",
    )


def _build_key_column(key: KeyDefinition) -> Column:  # type: ignore[type-arg]
    """Build a business or alternate key column."""
    col_type = _resolve_column_type(key.data_type, key)
    return Column(
        key.name,
        col_type,
        nullable=key.nullable,
        comment=key.description,
    )


def _build_attribute_column(attr: AttributeDefinition) -> Column:  # type: ignore[type-arg]
    """Build an attribute column."""
    col_type = _resolve_column_type(attr.data_type, attr)
    kwargs: dict = {
        "nullable": attr.nullable,
    }
    if attr.description:
        kwargs["comment"] = attr.description
    if attr.default and attr.default not in ("CURRENT_TIMESTAMP",):
        kwargs["server_default"] = attr.default
    return Column(attr.name, col_type, **kwargs)


def _build_common_column(col_def: CommonColumnDefinition) -> Column:  # type: ignore[type-arg]
    """Build a column from a common definition (audit/SCD)."""
    col_type = _resolve_column_type(col_def.data_type, col_def)
    kwargs: dict = {
        "nullable": col_def.nullable,
    }
    if col_def.description:
        kwargs["comment"] = col_def.description
    if col_def.default and col_def.default not in ("CURRENT_TIMESTAMP",):
        kwargs["server_default"] = col_def.default
    return Column(col_def.name, col_type, **kwargs)


def generate_table(
    entity_def: EntityDefinition,
    metadata: MetaData,
    common: CommonDefinitions | None = None,
) -> Table:
    """Generate a SQLAlchemy Table from an EntityDefinition.

    This creates the silver-layer (canonical) table.
    """
    columns: list[Column] = []  # type: ignore[type-arg]

    # Surrogate key
    columns.append(_build_surrogate_key_column(entity_def))

    # Business keys
    for bk in entity_def.keys.business:
        columns.append(_build_key_column(bk))

    # Alternate keys
    if entity_def.keys.alternate:
        for ak in entity_def.keys.alternate:
            columns.append(_build_key_column(ak))

    # Attributes
    for attr in entity_def.attributes:
        columns.append(_build_attribute_column(attr))

    # SCD Type 2 columns
    if common and entity_def.entity.scd_type == SCDType.TYPE2:
        for scd_col in common.scd_type2_columns:
            columns.append(_build_common_column(scd_col))

    # Audit columns
    if common and entity_def.entity.include_audit_columns:
        for audit_col in common.audit_columns:
            columns.append(_build_common_column(audit_col))

    table = Table(
        entity_def.entity.name,
        metadata,
        *columns,
        comment=entity_def.entity.description,
    )

    return table


def generate_ddl_sql(
    entity_def: EntityDefinition,
    common: CommonDefinitions | None = None,
    schema: str = "silver",
) -> str:
    """Generate DDL SQL string for an entity.

    Returns the CREATE TABLE statement as a string.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.schema import CreateTable

    metadata = MetaData(schema=schema)
    table = generate_table(entity_def, metadata, common)

    # Use a mock PostgreSQL dialect to render DDL
    mock_engine = create_engine(
        "postgresql+psycopg://", strategy="mock", executor=lambda *a, **kw: None
    )

    ddl = CreateTable(table).compile(dialect=mock_engine.dialect)
    return str(ddl).strip()


def generate_all_tables(
    entity_defs: list[EntityDefinition],
    metadata: MetaData,
    common: CommonDefinitions | None = None,
) -> dict[str, Table]:
    """Generate SQLAlchemy Tables for all entities.

    Returns a dict mapping entity name -> Table.
    """
    tables = {}
    for entity_def in entity_defs:
        table = generate_table(entity_def, metadata, common)
        tables[entity_def.entity.name] = table
    return tables
