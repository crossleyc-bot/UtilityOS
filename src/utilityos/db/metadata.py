"""Central SQLAlchemy MetaData registry for all data layers."""

from __future__ import annotations

from sqlalchemy import MetaData

from utilityos.common.types import DataLayer

# One MetaData instance per schema/layer
_metadata_registry: dict[DataLayer, MetaData] = {}


def get_metadata(layer: DataLayer) -> MetaData:
    """Get or create the MetaData for a given data layer."""
    if layer not in _metadata_registry:
        _metadata_registry[layer] = MetaData(schema=layer.value)
    return _metadata_registry[layer]


def get_all_metadata() -> dict[DataLayer, MetaData]:
    """Get all registered MetaData instances."""
    # Ensure all layers are initialized
    for layer in DataLayer:
        get_metadata(layer)
    return dict(_metadata_registry)


def clear_metadata() -> None:
    """Clear all metadata registries. Primarily for testing."""
    _metadata_registry.clear()
