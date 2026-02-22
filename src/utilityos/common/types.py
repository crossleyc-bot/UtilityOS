"""Shared type definitions and enums used across UtilityOS."""

from __future__ import annotations

from enum import Enum


class DataType(str, Enum):
    """Supported data types for canonical model attributes."""

    VARCHAR = "varchar"
    TEXT = "text"
    INTEGER = "integer"
    BIGINT = "bigint"
    SMALLINT = "smallint"
    NUMERIC = "numeric"
    BOOLEAN = "boolean"
    DATE = "date"
    TIMESTAMP = "timestamp"
    TIMESTAMP_TZ = "timestamp_tz"
    UUID = "uuid"
    JSONB = "jsonb"
    INTERVAL = "interval"


class SCDType(int, Enum):
    """Slowly Changing Dimension type."""

    NONE = 0
    TYPE1 = 1
    TYPE2 = 2


class PIIClassification(str, Enum):
    """PII sensitivity classification."""

    NONE = "none"
    DIRECT_IDENTIFIER = "direct_identifier"
    QUASI_IDENTIFIER = "quasi_identifier"
    SENSITIVE_IDENTIFIER = "sensitive_identifier"


class RelationshipType(str, Enum):
    """Entity relationship cardinality."""

    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_MANY = "many_to_many"


class PartitionStrategy(str, Enum):
    """Table partitioning strategy."""

    NONE = "none"
    RANGE = "range"
    LIST = "list"
    HASH = "hash"


class DataLayer(str, Enum):
    """Data warehouse layer."""

    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    META = "meta"


class PipelineStatus(str, Enum):
    """Pipeline execution status."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QualityCheckStatus(str, Enum):
    """Data quality check result status."""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    ERROR = "error"
