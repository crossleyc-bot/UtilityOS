"""Tests for YAML model loading and validation."""

from __future__ import annotations

import pytest

from utilityos.common.exceptions import ModelNotFoundError, ModelValidationError
from utilityos.models.loader import (
    discover_entity_files,
    load_common_definitions,
    load_entity_definition,
    load_enum_definitions,
)


class TestCommonLoader:
    def test_load_common_definitions(self, definitions_dir) -> None:
        common = load_common_definitions(definitions_dir)
        assert common.version == "1.0"
        assert len(common.audit_columns) >= 4

    def test_load_common_definitions_missing(self, tmp_path) -> None:
        with pytest.raises(ModelNotFoundError):
            load_common_definitions(tmp_path)


class TestEnumLoader:
    def test_load_enum_definitions(self, definitions_dir) -> None:
        enums = load_enum_definitions(definitions_dir)
        assert "customer_type" in enums.enums
        assert "customer_status" in enums.enums

    def test_load_enum_definitions_missing(self, tmp_path) -> None:
        with pytest.raises(ModelNotFoundError):
            load_enum_definitions(tmp_path)


class TestEntityLoader:
    def test_discover_entities(self, definitions_dir) -> None:
        names = discover_entity_files(definitions_dir)
        assert isinstance(names, list)
        # Should not include _common or _enums
        assert "_common" not in names
        assert "_enums" not in names

    def test_load_nonexistent_entity(self, definitions_dir) -> None:
        with pytest.raises(ModelNotFoundError):
            load_entity_definition("nonexistent_entity_xyz", definitions_dir)
