"""Effective dating and datetime utilities for UtilityOS."""

from __future__ import annotations

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return the current UTC datetime with timezone info."""
    return datetime.now(UTC)


# Sentinel value representing an open-ended effective_to date
EFFECTIVE_TO_MAX = datetime(9999, 12, 31, 23, 59, 59, tzinfo=UTC)


def is_current_record(effective_to: datetime | None) -> bool:
    """Check if a record is currently active (effective_to is NULL or max date)."""
    if effective_to is None:
        return True
    return effective_to >= EFFECTIVE_TO_MAX
