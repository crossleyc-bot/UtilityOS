"""Tests for DDL generation."""

from __future__ import annotations

import yaml
from sqlalchemy import MetaData

from utilityos.codegen.ddl_generator import generate_table
from utilityos.models.loader import load_common_definitions
from utilityos.models.schema import EntityDefinition


class TestDDLGenerator:
    def test_generate_table_basic(self, sample_entity_yaml: str) -> None:
        raw = yaml.safe_load(sample_entity_yaml)
        entity_def = EntityDefinition.model_validate(raw)
        metadata = MetaData(schema="silver")

        table = generate_table(entity_def, metadata)

        assert table.name == "test_entity"
        assert table.schema == "silver"
        column_names = {c.name for c in table.columns}
        assert "test_entity_sk" in column_names
        assert "test_id" in column_names
        assert "test_name" in column_names
        assert "test_value" in column_names

    def test_generate_table_with_common_columns(
        self, sample_entity_yaml: str, definitions_dir
    ) -> None:
        raw = yaml.safe_load(sample_entity_yaml)
        entity_def = EntityDefinition.model_validate(raw)
        common = load_common_definitions(definitions_dir)
        metadata = MetaData(schema="silver")

        table = generate_table(entity_def, metadata, common)

        column_names = {c.name for c in table.columns}
        # Should have SCD2 columns
        assert "effective_from" in column_names
        assert "effective_to" in column_names
        assert "is_current" in column_names
        assert "version_number" in column_names
        # Should have audit columns
        assert "created_at" in column_names
        assert "updated_at" in column_names
        assert "source_system" in column_names
        assert "batch_id" in column_names

    def test_surrogate_key_is_primary(self, sample_entity_yaml: str) -> None:
        raw = yaml.safe_load(sample_entity_yaml)
        entity_def = EntityDefinition.model_validate(raw)
        metadata = MetaData(schema="silver")

        table = generate_table(entity_def, metadata)

        pk_cols = [c.name for c in table.primary_key.columns]
        assert "test_entity_sk" in pk_cols

    def test_non_nullable_column(self, sample_entity_yaml: str) -> None:
        raw = yaml.safe_load(sample_entity_yaml)
        entity_def = EntityDefinition.model_validate(raw)
        metadata = MetaData(schema="silver")

        table = generate_table(entity_def, metadata)

        test_name_col = table.c.test_name
        assert test_name_col.nullable is False

    def test_nullable_column(self, sample_entity_yaml: str) -> None:
        raw = yaml.safe_load(sample_entity_yaml)
        entity_def = EntityDefinition.model_validate(raw)
        metadata = MetaData(schema="silver")

        table = generate_table(entity_def, metadata)

        test_value_col = table.c.test_value
        assert test_value_col.nullable is True
