"""Code normalization — map source system codes to canonical codes."""

from __future__ import annotations

from utilityos.common.exceptions import NormalizationError


class CodeNormalizer:
    """Normalizes source system codes to canonical values.

    Manages a registry of code maps keyed by (source_system, field_name).
    """

    def __init__(self) -> None:
        self._maps: dict[tuple[str, str], dict[str, str]] = {}

    def register_code_map(
        self,
        source_system: str,
        field_name: str,
        code_map: dict[str, str],
    ) -> None:
        """Register a code mapping for a source system and field."""
        self._maps[(source_system, field_name)] = code_map

    def normalize(
        self,
        source_system: str,
        field_name: str,
        value: str,
    ) -> str:
        """Normalize a source code value to its canonical equivalent."""
        key = (source_system, field_name)
        code_map = self._maps.get(key)
        if code_map is None:
            raise NormalizationError(
                f"No code map registered for ({source_system}, {field_name})"
            )

        normalized = value.strip()
        if normalized in code_map:
            return code_map[normalized]
        if "_default" in code_map:
            return code_map["_default"]

        raise NormalizationError(
            f"No mapping for value '{normalized}' "
            f"in ({source_system}, {field_name})"
        )
