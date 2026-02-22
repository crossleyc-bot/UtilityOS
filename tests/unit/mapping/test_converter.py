"""Tests for unit conversion."""

from __future__ import annotations

import pytest

from utilityos.common.exceptions import TransformationError
from utilityos.mapping.converter import convert_units


class TestUnitConversion:
    def test_identity(self) -> None:
        assert convert_units(100.0, "KWH", "KWH") == 100.0

    def test_kwh_to_mwh(self) -> None:
        assert convert_units(1000.0, "KWH", "MWH") == 1.0

    def test_gal_to_kgal(self) -> None:
        assert convert_units(1000.0, "GAL", "KGAL") == 1.0

    def test_ccf_to_gal(self) -> None:
        result = convert_units(1.0, "CCF", "GAL")
        assert abs(result - 748.052) < 0.01

    def test_case_insensitive(self) -> None:
        assert convert_units(1000.0, "kwh", "mwh") == 1.0

    def test_unknown_conversion_raises(self) -> None:
        with pytest.raises(TransformationError):
            convert_units(1.0, "KWH", "LITERS")
