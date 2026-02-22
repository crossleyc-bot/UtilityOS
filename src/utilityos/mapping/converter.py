"""Unit conversion for utility measurements."""

from __future__ import annotations

from utilityos.common.exceptions import TransformationError

# Conversion factors: (from_unit, to_unit) -> multiplier
_CONVERSIONS: dict[tuple[str, str], float] = {
    # Volume
    ("GAL", "KGAL"): 0.001,
    ("KGAL", "GAL"): 1000.0,
    ("GAL", "CF"): 0.133681,
    ("CF", "GAL"): 7.48052,
    ("CCF", "GAL"): 748.052,
    ("GAL", "CCF"): 0.001337,
    ("CCF", "CF"): 100.0,
    ("CF", "CCF"): 0.01,
    ("CCF", "KGAL"): 0.748052,
    ("KGAL", "CCF"): 1.33681,
    ("MCF", "CF"): 1000.0,
    ("CF", "MCF"): 0.001,
    # Energy
    ("KWH", "MWH"): 0.001,
    ("MWH", "KWH"): 1000.0,
    ("THERM", "KWH"): 29.3001,
    ("KWH", "THERM"): 0.034130,
    ("MCF", "THERM"): 10.37,
    ("THERM", "MCF"): 0.09643,
    # Identity
    ("KWH", "KWH"): 1.0,
    ("GAL", "GAL"): 1.0,
    ("CF", "CF"): 1.0,
    ("CCF", "CCF"): 1.0,
    ("KGAL", "KGAL"): 1.0,
    ("KW", "KW"): 1.0,
    ("THERM", "THERM"): 1.0,
    ("MCF", "MCF"): 1.0,
}


def convert_units(
    value: float,
    from_unit: str,
    to_unit: str,
) -> float:
    """Convert a value between measurement units."""
    from_upper = from_unit.upper()
    to_upper = to_unit.upper()

    if from_upper == to_upper:
        return value

    key = (from_upper, to_upper)
    factor = _CONVERSIONS.get(key)
    if factor is None:
        raise TransformationError(
            f"No conversion defined from '{from_unit}' to '{to_unit}'"
        )

    return value * factor
