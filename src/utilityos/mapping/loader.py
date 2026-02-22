"""Load source mapping definitions from YAML."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from utilityos.common.exceptions import MappingValidationError, ModelNotFoundError
from utilityos.mapping.schema import MappingDefinition

_MAPPINGS_DIR = Path(__file__).parent / "definitions"


def load_mapping(
    mapping_name: str,
    mappings_dir: Path | None = None,
) -> MappingDefinition:
    """Load and validate a source mapping definition."""
    mdir = mappings_dir or _MAPPINGS_DIR
    path = mdir / f"{mapping_name}.yaml"
    if not path.exists():
        raise ModelNotFoundError(f"Mapping definition not found: {path}")

    with open(path) as f:
        raw = yaml.safe_load(f)

    try:
        return MappingDefinition.model_validate(raw)
    except ValidationError as e:
        raise MappingValidationError(
            f"Invalid mapping definition '{mapping_name}': {e}"
        ) from e


def discover_mappings(
    mappings_dir: Path | None = None,
) -> list[str]:
    """Discover all mapping definition files."""
    mdir = mappings_dir or _MAPPINGS_DIR
    return sorted(p.stem for p in mdir.glob("*.yaml") if not p.name.startswith("_"))
