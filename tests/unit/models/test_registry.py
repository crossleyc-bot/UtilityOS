"""Tests for the entity model registry."""

from __future__ import annotations

import pytest
import yaml

from utilityos.common.exceptions import ModelNotFoundError
from utilityos.models.registry import ModelRegistry
from utilityos.models.schema import EntityDefinition


@pytest.fixture
def registry_with_entity(sample_entity_yaml: str) -> ModelRegistry:
    raw = yaml.safe_load(sample_entity_yaml)
    entity = EntityDefinition.model_validate(raw)
    registry = ModelRegistry()
    registry.register(entity)
    return registry


class TestModelRegistry:
    def test_register_and_get(self, registry_with_entity: ModelRegistry) -> None:
        entity = registry_with_entity.get("test_entity")
        assert entity.entity.name == "test_entity"

    def test_get_missing_raises(self, registry_with_entity: ModelRegistry) -> None:
        with pytest.raises(ModelNotFoundError):
            registry_with_entity.get("nonexistent")

    def test_list_entities(self, registry_with_entity: ModelRegistry) -> None:
        names = registry_with_entity.list_entities()
        assert names == ["test_entity"]

    def test_list_by_domain(self, registry_with_entity: ModelRegistry) -> None:
        names = registry_with_entity.list_by_domain("testing")
        assert "test_entity" in names

    def test_list_domains(self, registry_with_entity: ModelRegistry) -> None:
        domains = registry_with_entity.list_domains()
        assert "testing" in domains

    def test_len(self, registry_with_entity: ModelRegistry) -> None:
        assert len(registry_with_entity) == 1

    def test_contains(self, registry_with_entity: ModelRegistry) -> None:
        assert "test_entity" in registry_with_entity
        assert "other" not in registry_with_entity
