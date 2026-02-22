"""Tests for Pydantic model schema validation."""

from __future__ import annotations

import pytest
import yaml

from utilityos.common.types import DataType, SCDType
from utilityos.models.schema import (
    AttributeDefinition,
    CommonDefinitions,
    EntityDefinition,
    EntityMetadata,
    EnumDefinitions,
    KeyDefinition,
    KeysBlock,
)


class TestEntityDefinition:
    def test_valid_entity_from_yaml(self, sample_entity_yaml: str) -> None:
        raw = yaml.safe_load(sample_entity_yaml)
        entity = EntityDefinition.model_validate(raw)
        assert entity.entity.name == "test_entity"
        assert entity.entity.scd_type == SCDType.TYPE2
        assert len(entity.attributes) == 2
        assert entity.keys.surrogate.name == "test_entity_sk"

    def test_entity_metadata_defaults(self) -> None:
        meta = EntityMetadata(
            name="test",
            display_name="Test",
            description="desc",
            domain="testing",
            version="1.0.0",
        )
        assert meta.scd_type == SCDType.TYPE2
        assert meta.include_audit_columns is True

    def test_attribute_defaults(self) -> None:
        attr = AttributeDefinition(name="col", data_type=DataType.VARCHAR)
        assert attr.nullable is True
        assert attr.pii is False
        assert attr.length is None

    def test_key_definition(self) -> None:
        key = KeyDefinition(
            name="test_sk",
            data_type=DataType.BIGINT,
            generated="ALWAYS AS IDENTITY",
        )
        assert key.data_type == DataType.BIGINT
        assert key.nullable is False

    def test_invalid_data_type_rejected(self) -> None:
        with pytest.raises(Exception):
            AttributeDefinition(name="col", data_type="invalid_type")

    def test_entity_with_relationships(self) -> None:
        raw = {
            "entity": {
                "name": "test",
                "display_name": "Test",
                "description": "desc",
                "domain": "testing",
                "version": "1.0.0",
            },
            "keys": {
                "surrogate": {"name": "test_sk", "data_type": "bigint"},
                "business": [{"name": "test_id", "data_type": "varchar", "length": 50}],
            },
            "attributes": [
                {"name": "name", "data_type": "varchar", "length": 100},
            ],
            "relationships": [
                {
                    "name": "children",
                    "target_entity": "child",
                    "type": "one_to_many",
                    "foreign_key_on": "child",
                    "foreign_key_column": "test_sk",
                }
            ],
        }
        entity = EntityDefinition.model_validate(raw)
        assert len(entity.relationships) == 1
        assert entity.relationships[0].target_entity == "child"

    def test_entity_with_quality_rules(self) -> None:
        raw = {
            "entity": {
                "name": "test",
                "display_name": "Test",
                "description": "desc",
                "domain": "testing",
                "version": "1.0.0",
            },
            "keys": {
                "surrogate": {"name": "test_sk", "data_type": "bigint"},
                "business": [{"name": "test_id", "data_type": "varchar", "length": 50}],
            },
            "attributes": [
                {"name": "status", "data_type": "varchar", "length": 30, "nullable": False},
            ],
            "quality_rules": [
                {"rule": "not_null", "columns": ["status"]},
                {"rule": "enum_valid", "column": "status", "enum_ref": "test_status"},
            ],
        }
        entity = EntityDefinition.model_validate(raw)
        assert len(entity.quality_rules) == 2


class TestCommonDefinitions:
    def test_load_common_yaml(self, definitions_dir) -> None:
        path = definitions_dir / "_common.yaml"
        if not path.exists():
            pytest.skip("_common.yaml not found")
        with open(path) as f:
            raw = yaml.safe_load(f)
        common = CommonDefinitions.model_validate(raw)
        assert len(common.audit_columns) > 0
        assert len(common.scd_type2_columns) > 0
        assert common.surrogate_key_column.data_type == DataType.BIGINT


class TestEnumDefinitions:
    def test_load_enums_yaml(self, definitions_dir) -> None:
        path = definitions_dir / "_enums.yaml"
        if not path.exists():
            pytest.skip("_enums.yaml not found")
        with open(path) as f:
            raw = yaml.safe_load(f)
        enums = EnumDefinitions.model_validate(raw)
        assert "customer_type" in enums.enums
        assert len(enums.enums["customer_type"].values) > 0
