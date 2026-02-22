"""Load and validate YAML model definitions."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from utilityos.common.exceptions import ModelNotFoundError, ModelValidationError
from utilityos.models.schema import (
    CommonDefinitions,
    EntityDefinition,
    EnumDefinitions,
)

_DEFINITIONS_DIR = Path(__file__).parent / "definitions"


def get_definitions_dir() -> Path:
    """Return the path to the YAML definitions directory."""
    return _DEFINITIONS_DIR


def load_common_definitions(
    definitions_dir: Path | None = None,
) -> CommonDefinitions:
    """Load and validate _common.yaml."""
    defs_dir = definitions_dir or _DEFINITIONS_DIR
    path = defs_dir / "_common.yaml"
    if not path.exists():
        raise ModelNotFoundError(f"Common definitions not found: {path}")

    with open(path) as f:
        raw = yaml.safe_load(f)

    try:
        return CommonDefinitions.model_validate(raw)
    except ValidationError as e:
        raise ModelValidationError(
            f"Invalid common definitions in {path}: {e}"
        ) from e


def load_enum_definitions(
    definitions_dir: Path | None = None,
) -> EnumDefinitions:
    """Load and validate _enums.yaml."""
    defs_dir = definitions_dir or _DEFINITIONS_DIR
    path = defs_dir / "_enums.yaml"
    if not path.exists():
        raise ModelNotFoundError(f"Enum definitions not found: {path}")

    with open(path) as f:
        raw = yaml.safe_load(f)

    try:
        return EnumDefinitions.model_validate(raw)
    except ValidationError as e:
        raise ModelValidationError(
            f"Invalid enum definitions in {path}: {e}"
        ) from e


def load_entity_definition(
    entity_name: str,
    definitions_dir: Path | None = None,
) -> EntityDefinition:
    """Load and validate a single entity YAML definition."""
    defs_dir = definitions_dir or _DEFINITIONS_DIR
    path = defs_dir / f"{entity_name}.yaml"
    if not path.exists():
        raise ModelNotFoundError(f"Entity definition not found: {path}")

    with open(path) as f:
        raw = yaml.safe_load(f)

    try:
        return EntityDefinition.model_validate(raw)
    except ValidationError as e:
        raise ModelValidationError(
            f"Invalid entity definition for '{entity_name}' in {path}: {e}"
        ) from e


def discover_entity_files(
    definitions_dir: Path | None = None,
) -> list[str]:
    """Discover all entity YAML files (excluding _ prefixed files)."""
    defs_dir = definitions_dir or _DEFINITIONS_DIR
    entity_names = []
    for path in sorted(defs_dir.glob("*.yaml")):
        if path.name.startswith("_"):
            continue
        entity_names.append(path.stem)
    return entity_names


def load_all_entities(
    definitions_dir: Path | None = None,
) -> list[EntityDefinition]:
    """Load and validate all entity definitions.

    Returns a list of validated EntityDefinition objects.
    Raises ModelValidationError if any definition is invalid.
    """
    defs_dir = definitions_dir or _DEFINITIONS_DIR
    entity_names = discover_entity_files(defs_dir)
    entities = []
    errors: list[str] = []

    for name in entity_names:
        try:
            entity = load_entity_definition(name, defs_dir)
            entities.append(entity)
        except (ModelValidationError, ModelNotFoundError) as e:
            errors.append(str(e))

    if errors:
        raise ModelValidationError(
            f"Failed to load {len(errors)} entity definitions:\n"
            + "\n".join(f"  - {e}" for e in errors)
        )

    return entities
