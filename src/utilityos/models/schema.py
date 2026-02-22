"""Pydantic models for validating YAML canonical model definitions.

This is the 'schema of the schema' — it ensures every YAML entity definition
is well-formed before DDL generation, pipeline execution, or quality checks.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from utilityos.common.types import (
    DataType,
    PartitionStrategy,
    PIIClassification,
    RelationshipType,
    SCDType,
)


class AttributeDefinition(BaseModel):
    """A single attribute (column) in an entity."""

    name: str
    data_type: DataType
    length: int | None = None
    precision: int | None = None
    scale: int | None = None
    nullable: bool = True
    default: str | None = None
    description: str = ""
    pii: bool = False
    pii_classification: PIIClassification = PIIClassification.NONE
    enum_ref: str | None = None


class KeyDefinition(BaseModel):
    """A key column (surrogate, business, or alternate)."""

    name: str
    data_type: DataType
    length: int | None = None
    generated: str | None = None
    description: str = ""
    source_of_truth: bool = False
    nullable: bool = False


class RelationshipDefinition(BaseModel):
    """A relationship between two entities."""

    name: str
    target_entity: str
    type: RelationshipType
    foreign_key_on: str | None = None
    foreign_key_column: str | None = None
    through_entity: str | None = None
    description: str = ""
    integrity: str = "optional"


class IndexDefinition(BaseModel):
    """An index on one or more columns."""

    columns: list[str]
    unique: bool = False
    where: str | None = None


class QualityRuleDefinition(BaseModel):
    """An inline quality rule for an entity."""

    rule: str
    columns: list[str] | None = None
    column: str | None = None
    enum_ref: str | None = None
    condition: str | None = None
    scope: str | None = None
    message: str | None = None
    min_value: float | None = None
    max_value: float | None = None


class GoldLayerDefinition(BaseModel):
    """Gold layer configuration for an entity."""

    dimension: bool = False
    dimension_type: str | None = None
    fact: bool = False
    grain: list[str] | None = None
    measures: list[str] | None = None


class PartitionDefinition(BaseModel):
    """Table partitioning configuration."""

    strategy: PartitionStrategy = PartitionStrategy.NONE
    column: str | None = None
    interval: str | None = None


class EntityMetadata(BaseModel):
    """Core metadata about an entity."""

    name: str
    display_name: str
    description: str
    domain: str
    version: str
    scd_type: SCDType = SCDType.TYPE2
    include_audit_columns: bool = True


class KeysBlock(BaseModel):
    """The keys section of an entity definition."""

    surrogate: KeyDefinition
    business: list[KeyDefinition]
    alternate: list[KeyDefinition] | None = None


class EntityDefinition(BaseModel):
    """Complete validated representation of a YAML entity definition."""

    entity: EntityMetadata
    keys: KeysBlock
    attributes: list[AttributeDefinition]
    relationships: list[RelationshipDefinition] | None = None
    indexes: list[IndexDefinition] | None = None
    quality_rules: list[QualityRuleDefinition] | None = None
    partitioning: PartitionDefinition | None = None
    gold_layer: GoldLayerDefinition | None = None


# --- Common definitions schema ---


class CommonColumnDefinition(BaseModel):
    """A column definition from _common.yaml."""

    name: str
    data_type: DataType
    length: int | None = None
    nullable: bool = True
    default: str | None = None
    description: str = ""
    generated: str | None = None


class SurrogateKeyTemplate(BaseModel):
    """Template for surrogate key columns from _common.yaml."""

    name: str = Field(description="Name template, e.g. '{entity}_sk'")
    data_type: DataType
    generated: str | None = None
    description: str = ""


class CommonDefinitions(BaseModel):
    """Validated representation of _common.yaml."""

    version: str
    audit_columns: list[CommonColumnDefinition]
    scd_type2_columns: list[CommonColumnDefinition]
    surrogate_key_column: SurrogateKeyTemplate


# --- Enum definitions schema ---


class EnumValue(BaseModel):
    """A single value in an enum set."""

    code: str
    label: str
    description: str = ""


class EnumDefinition(BaseModel):
    """A named enum/code set."""

    description: str = ""
    values: list[EnumValue]


class EnumDefinitions(BaseModel):
    """Validated representation of _enums.yaml."""

    version: str
    enums: dict[str, EnumDefinition]
