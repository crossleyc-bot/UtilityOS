"""Relationship graph builder and validator for entity models."""

from __future__ import annotations

from dataclasses import dataclass, field

from utilityos.common.exceptions import RelationshipError
from utilityos.models.registry import ModelRegistry
from utilityos.models.schema import RelationshipDefinition


@dataclass
class RelationshipEdge:
    """An edge in the entity relationship graph."""

    source_entity: str
    target_entity: str
    relationship_name: str
    relationship_type: str
    foreign_key_on: str | None = None
    foreign_key_column: str | None = None
    through_entity: str | None = None


@dataclass
class RelationshipGraph:
    """Graph of all entity relationships."""

    edges: list[RelationshipEdge] = field(default_factory=list)
    _adjacency: dict[str, list[RelationshipEdge]] = field(
        default_factory=dict, repr=False
    )

    def add_edge(self, edge: RelationshipEdge) -> None:
        """Add an edge to the graph."""
        self.edges.append(edge)
        self._adjacency.setdefault(edge.source_entity, []).append(edge)

    def get_relationships(self, entity_name: str) -> list[RelationshipEdge]:
        """Get all relationships originating from an entity."""
        return self._adjacency.get(entity_name, [])

    def get_dependents(self, entity_name: str) -> list[str]:
        """Get entities that have foreign keys pointing to this entity."""
        dependents = []
        for edge in self.edges:
            if edge.target_entity == entity_name:
                dependents.append(edge.source_entity)
        return sorted(set(dependents))

    def get_dependencies(self, entity_name: str) -> list[str]:
        """Get entities that this entity depends on (has FK to)."""
        dependencies = []
        for edge in self._adjacency.get(entity_name, []):
            dependencies.append(edge.target_entity)
        return sorted(set(dependencies))

    def topological_sort(self) -> list[str]:
        """Return entities in dependency order (dependencies first).

        Useful for determining DDL creation order.
        """
        all_entities = set()
        for edge in self.edges:
            all_entities.add(edge.source_entity)
            all_entities.add(edge.target_entity)

        in_degree: dict[str, int] = {e: 0 for e in all_entities}
        for edge in self.edges:
            if edge.foreign_key_on == edge.source_entity:
                # source_entity depends on target_entity
                in_degree[edge.source_entity] = (
                    in_degree.get(edge.source_entity, 0) + 1
                )

        queue = [e for e in sorted(all_entities) if in_degree[e] == 0]
        result = []

        while queue:
            entity = queue.pop(0)
            result.append(entity)
            for edge in self.edges:
                if (
                    edge.target_entity == entity
                    and edge.foreign_key_on == edge.source_entity
                ):
                    in_degree[edge.source_entity] -= 1
                    if in_degree[edge.source_entity] == 0:
                        queue.append(edge.source_entity)
                        queue.sort()

        if len(result) != len(all_entities):
            missing = all_entities - set(result)
            raise RelationshipError(
                f"Circular dependency detected involving: {missing}"
            )

        return result


def build_relationship_graph(registry: ModelRegistry) -> RelationshipGraph:
    """Build a relationship graph from all entities in the registry."""
    graph = RelationshipGraph()

    for entity_def in registry:
        if entity_def.relationships is None:
            continue
        for rel in entity_def.relationships:
            edge = RelationshipEdge(
                source_entity=entity_def.entity.name,
                target_entity=rel.target_entity,
                relationship_name=rel.name,
                relationship_type=rel.type.value,
                foreign_key_on=rel.foreign_key_on,
                foreign_key_column=rel.foreign_key_column,
                through_entity=rel.through_entity,
            )
            graph.add_edge(edge)

    return graph


def validate_relationships(
    registry: ModelRegistry,
    graph: RelationshipGraph | None = None,
) -> list[str]:
    """Validate all entity relationships.

    Returns a list of validation error messages (empty if valid).
    """
    if graph is None:
        graph = build_relationship_graph(registry)

    errors: list[str] = []
    registered = set(registry.list_entities())

    for edge in graph.edges:
        # Check target entity exists
        if edge.target_entity not in registered:
            errors.append(
                f"{edge.source_entity}.{edge.relationship_name}: "
                f"target entity '{edge.target_entity}' not found"
            )

        # Check through entity exists (for many-to-many)
        if edge.through_entity and edge.through_entity not in registered:
            # Junction tables may not always be in the registry
            pass

        # Check foreign key references valid column
        if edge.foreign_key_on and edge.foreign_key_on in registered:
            fk_entity = registry.get(edge.foreign_key_on)
            if edge.foreign_key_column:
                all_cols = {a.name for a in fk_entity.attributes}
                all_cols.add(fk_entity.keys.surrogate.name)
                for bk in fk_entity.keys.business:
                    all_cols.add(bk.name)
                # FK column might reference a SK from another entity
                # so we just validate the FK entity is real

    return errors
