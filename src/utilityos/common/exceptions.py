"""Custom exception hierarchy for UtilityOS."""

from __future__ import annotations


class UtilityOSError(Exception):
    """Base exception for all UtilityOS errors."""


# Model-related errors
class ModelError(UtilityOSError):
    """Base for model definition errors."""


class ModelValidationError(ModelError):
    """Raised when a YAML model definition fails validation."""


class ModelNotFoundError(ModelError):
    """Raised when a referenced entity model does not exist."""


class RelationshipError(ModelError):
    """Raised when entity relationships are invalid."""


# Code generation errors
class CodegenError(UtilityOSError):
    """Base for code generation errors."""


class DDLGenerationError(CodegenError):
    """Raised when DDL generation fails."""


class MigrationError(CodegenError):
    """Raised when migration operations fail."""


# Pipeline errors
class PipelineError(UtilityOSError):
    """Base for pipeline errors."""


class PipelineStepError(PipelineError):
    """Raised when a pipeline step fails."""


class SourceConnectionError(PipelineError):
    """Raised when a source system connection fails."""


class ExtractionError(PipelineError):
    """Raised when data extraction fails."""


class TransformationError(PipelineError):
    """Raised when data transformation fails."""


class LoadError(PipelineError):
    """Raised when data loading fails."""


# Mapping errors
class MappingError(UtilityOSError):
    """Base for source mapping errors."""


class MappingValidationError(MappingError):
    """Raised when a source mapping definition is invalid."""


class NormalizationError(MappingError):
    """Raised when code normalization fails."""


# Quality errors
class QualityCheckError(UtilityOSError):
    """Base for data quality errors."""


# Database errors
class DatabaseError(UtilityOSError):
    """Base for database connection/operation errors."""


class SchemaError(DatabaseError):
    """Raised when schema operations fail."""


# Configuration errors
class ConfigurationError(UtilityOSError):
    """Raised when configuration is invalid or missing."""
