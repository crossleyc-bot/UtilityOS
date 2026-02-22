"""Central registry of all loaded entity models."""

from __future__ import annotations

from utilityos.common.exceptions import ModelNotFoundError
from utilityos.models.schema import (
    CommonDefinitions,
    EntityDefinition,
    EnumDefinitions,
)


class ModelRegistry:
    """Central registry for canonical model definitions.

    Provides lookup by entity name, domain listing, and
    relationship traversal.
    """

    def __init__(self) -> None:
        self._entities: dict[str, EntityDefinition] = {}
        self._common: CommonDefinitions | None = None
        self._enums: EnumDefinitions | None = None

    @property
    def common(self) -> CommonDefinitions:
        """Get common definitions. Raises if not loaded."""
        if self._common is None:
            raise ModelNotFoundError("Common definitions not loaded")
        return self._common

    @property
    def enums(self) -> EnumDefinitions:
        """Get enum definitions. Raises if not loaded."""
        if self._enums is None:
            raise ModelNotFoundError("Enum definitions not loaded")
        return self._enums

    def set_common(self, common: CommonDefinitions) -> None:
        """Register common definitions."""
        self._common = common

    def set_enums(self, enums: EnumDefinitions) -> None:
        """Register enum definitions."""
        self._enums = enums

    def register(self, entity: EntityDefinition) -> None:
        """Register an entity definition."""
        self._entities[entity.entity.name] = entity

    def get(self, entity_name: str) -> EntityDefinition:
        """Get an entity definition by name."""
        if entity_name not in self._entities:
            raise ModelNotFoundError(
                f"Entity '{entity_name}' not found in registry. "
                f"Available: {', '.join(sorted(self._entities.keys()))}"
            )
        return self._entities[entity_name]

    def list_entities(self) -> list[str]:
        """List all registered entity names."""
        return sorted(self._entities.keys())

    def list_by_domain(self, domain: str) -> list[str]:
        """List entity names belonging to a domain."""
        return sorted(
            name
            for name, defn in self._entities.items()
            if defn.entity.domain == domain
        )

    def list_domains(self) -> list[str]:
        """List all unique domains."""
        return sorted({defn.entity.domain for defn in self._entities.values()})

    def get_enum_values(self, enum_name: str) -> list[str]:
        """Get the valid code values for a named enum."""
        if self._enums is None:
            raise ModelNotFoundError("Enum definitions not loaded")
        if enum_name not in self._enums.enums:
            raise ModelNotFoundError(f"Enum '{enum_name}' not found")
        return [v.code for v in self._enums.enums[enum_name].values]

    def __len__(self) -> int:
        return len(self._entities)

    def __contains__(self, entity_name: str) -> bool:
        return entity_name in self._entities

    def __iter__(self):  # noqa: ANN204
        return iter(self._entities.values())
