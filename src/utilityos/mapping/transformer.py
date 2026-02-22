"""Apply field-level transformations defined in source mappings."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from utilityos.common.exceptions import TransformationError
from utilityos.mapping.schema import FieldMapping


def apply_transform(value: Any, field_mapping: FieldMapping) -> Any:
    """Apply the transform chain to a single value.

    Transforms are specified as pipe-separated operations:
    e.g., 'trim|uppercase' or 'code_map' or 'date_parse'
    """
    if field_mapping.transform is None:
        return value

    transforms = field_mapping.transform.split("|")
    result = value

    for transform_name in transforms:
        transform_name = transform_name.strip()
        result = _apply_single_transform(result, transform_name, field_mapping)

    return result


def _apply_single_transform(
    value: Any,
    transform_name: str,
    field_mapping: FieldMapping,
) -> Any:
    """Apply a single named transform to a value."""
    if value is None:
        return None

    transform_fn = _TRANSFORMS.get(transform_name)
    if transform_fn is None:
        raise TransformationError(
            f"Unknown transform: '{transform_name}' "
            f"for field '{field_mapping.target}'"
        )
    return transform_fn(value, field_mapping)


def _transform_trim(value: Any, _: FieldMapping) -> Any:
    if isinstance(value, str):
        return value.strip()
    return value


def _transform_uppercase(value: Any, _: FieldMapping) -> Any:
    if isinstance(value, str):
        return value.upper()
    return value


def _transform_lowercase(value: Any, _: FieldMapping) -> Any:
    if isinstance(value, str):
        return value.lower()
    return value


def _transform_title_case(value: Any, _: FieldMapping) -> Any:
    if isinstance(value, str):
        return value.title()
    return value


def _transform_null_if_empty(value: Any, _: FieldMapping) -> Any:
    if isinstance(value, str) and value.strip() == "":
        return None
    return value


def _transform_code_map(value: Any, mapping: FieldMapping) -> Any:
    if mapping.code_map is None:
        raise TransformationError(
            f"code_map transform requires code_map definition "
            f"for field '{mapping.target}'"
        )
    str_value = str(value).strip()
    if str_value in mapping.code_map:
        return mapping.code_map[str_value]
    if "_default" in mapping.code_map:
        return mapping.code_map["_default"]
    raise TransformationError(
        f"No code_map entry for value '{str_value}' "
        f"in field '{mapping.target}'"
    )


def _transform_date_parse(value: Any, mapping: FieldMapping) -> Any:
    if not isinstance(value, str):
        return value
    fmt = mapping.format or "%Y-%m-%d"
    try:
        return datetime.strptime(value.strip(), fmt).date()
    except ValueError as e:
        raise TransformationError(
            f"Failed to parse date '{value}' with format '{fmt}' "
            f"for field '{mapping.target}': {e}"
        ) from e


def _transform_phone_normalize(value: Any, _: FieldMapping) -> Any:
    if not isinstance(value, str):
        return value
    digits = re.sub(r"[^\d]", "", value)
    if len(digits) == 10:
        return f"+1{digits}"
    if len(digits) == 11 and digits.startswith("1"):
        return f"+{digits}"
    return digits


# Registry of available transforms
_TRANSFORMS = {
    "trim": _transform_trim,
    "uppercase": _transform_uppercase,
    "lowercase": _transform_lowercase,
    "title_case": _transform_title_case,
    "null_if_empty": _transform_null_if_empty,
    "code_map": _transform_code_map,
    "date_parse": _transform_date_parse,
    "phone_normalize": _transform_phone_normalize,
}


def apply_field_mappings(
    source_row: dict[str, Any],
    field_mappings: list[FieldMapping],
) -> dict[str, Any]:
    """Apply all field mappings to a source row, producing a target row."""
    target_row: dict[str, Any] = {}

    for fm in field_mappings:
        if fm.source is None:
            # Computed field — skip for now (requires expression evaluation)
            continue
        raw_value = source_row.get(fm.source)
        target_row[fm.target] = apply_transform(raw_value, fm)

    return target_row
