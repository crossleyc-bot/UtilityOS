"""Tests for source mapping transformations."""

from __future__ import annotations

from datetime import date

import pytest

from utilityos.common.exceptions import TransformationError
from utilityos.mapping.schema import FieldMapping
from utilityos.mapping.transformer import apply_field_mappings, apply_transform


class TestTransforms:
    def test_trim(self) -> None:
        fm = FieldMapping(source="a", target="b", transform="trim")
        assert apply_transform("  hello  ", fm) == "hello"

    def test_uppercase(self) -> None:
        fm = FieldMapping(source="a", target="b", transform="uppercase")
        assert apply_transform("hello", fm) == "HELLO"

    def test_lowercase(self) -> None:
        fm = FieldMapping(source="a", target="b", transform="lowercase")
        assert apply_transform("HELLO", fm) == "hello"

    def test_title_case(self) -> None:
        fm = FieldMapping(source="a", target="b", transform="title_case")
        assert apply_transform("john doe", fm) == "John Doe"

    def test_null_if_empty(self) -> None:
        fm = FieldMapping(source="a", target="b", transform="null_if_empty")
        assert apply_transform("  ", fm) is None
        assert apply_transform("hello", fm) == "hello"

    def test_code_map(self) -> None:
        fm = FieldMapping(
            source="a",
            target="b",
            transform="code_map",
            code_map={"R": "RESIDENTIAL", "C": "COMMERCIAL", "_default": "OTHER"},
        )
        assert apply_transform("R", fm) == "RESIDENTIAL"
        assert apply_transform("C", fm) == "COMMERCIAL"
        assert apply_transform("X", fm) == "OTHER"

    def test_code_map_missing_raises(self) -> None:
        fm = FieldMapping(
            source="a",
            target="b",
            transform="code_map",
            code_map={"R": "RESIDENTIAL"},
        )
        with pytest.raises(TransformationError):
            apply_transform("X", fm)

    def test_date_parse(self) -> None:
        fm = FieldMapping(
            source="a", target="b", transform="date_parse", format="%m/%d/%Y"
        )
        result = apply_transform("01/15/2024", fm)
        assert result == date(2024, 1, 15)

    def test_phone_normalize(self) -> None:
        fm = FieldMapping(source="a", target="b", transform="phone_normalize")
        assert apply_transform("(555) 123-4567", fm) == "+15551234567"

    def test_chained_transforms(self) -> None:
        fm = FieldMapping(source="a", target="b", transform="trim|uppercase")
        assert apply_transform("  hello  ", fm) == "HELLO"

    def test_none_passthrough(self) -> None:
        fm = FieldMapping(source="a", target="b", transform="trim")
        assert apply_transform(None, fm) is None

    def test_no_transform(self) -> None:
        fm = FieldMapping(source="a", target="b")
        assert apply_transform("hello", fm) == "hello"

    def test_unknown_transform_raises(self) -> None:
        fm = FieldMapping(source="a", target="b", transform="nonexistent")
        with pytest.raises(TransformationError):
            apply_transform("hello", fm)


class TestApplyFieldMappings:
    def test_basic_mapping(self) -> None:
        source_row = {"CUST_NO": "12345", "FNAME": "  john  "}
        mappings = [
            FieldMapping(source="CUST_NO", target="customer_number", transform="trim"),
            FieldMapping(source="FNAME", target="first_name", transform="trim|title_case"),
        ]
        result = apply_field_mappings(source_row, mappings)
        assert result == {"customer_number": "12345", "first_name": "John"}

    def test_missing_source_column(self) -> None:
        source_row = {"A": "1"}
        mappings = [
            FieldMapping(source="B", target="c", transform="trim"),
        ]
        result = apply_field_mappings(source_row, mappings)
        assert result == {"c": None}

    def test_computed_field_skipped(self) -> None:
        source_row = {"A": "1"}
        mappings = [
            FieldMapping(source=None, target="computed_col", transform="computed"),
        ]
        result = apply_field_mappings(source_row, mappings)
        assert result == {}
