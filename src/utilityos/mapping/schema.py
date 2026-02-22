"""Pydantic models for source mapping definitions."""

from __future__ import annotations

from pydantic import BaseModel


class CodeMapEntry(BaseModel):
    """A single code mapping (source code -> canonical code)."""
    # Defined inline in field mappings


class FieldMapping(BaseModel):
    """A single field-level mapping from source to target."""

    source: str | None = None
    target: str
    transform: str | None = None
    code_map: dict[str, str] | None = None
    format: str | None = None
    expression: str | None = None
    from_unit: str | None = None
    to_unit: str | None = None


class IncrementalConfig(BaseModel):
    """Incremental load configuration."""

    strategy: str = "full_replace"  # full_replace, modified_date, cdc_log
    column: str | None = None
    format: str | None = None


class IdentityResolutionConfig(BaseModel):
    """Identity resolution configuration."""

    match_on: list[str]
    fuzzy_match: bool = False


class MappingMetadata(BaseModel):
    """Metadata about a source mapping."""

    name: str
    source_system: str
    source_table: str
    target_entity: str
    version: str = "1.0.0"
    description: str = ""


class MappingDefinition(BaseModel):
    """Complete source mapping definition."""

    mapping: MappingMetadata
    field_mappings: list[FieldMapping]
    identity_resolution: IdentityResolutionConfig | None = None
    incremental: IncrementalConfig | None = None
