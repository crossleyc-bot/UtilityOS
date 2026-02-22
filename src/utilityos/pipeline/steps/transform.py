"""Source mapping transformation step."""

from __future__ import annotations

from utilityos.common.exceptions import MappingValidationError, TransformationError
from utilityos.mapping.loader import load_mapping
from utilityos.mapping.transformer import apply_field_mappings
from utilityos.pipeline.context import PipelineContext
from utilityos.pipeline.step import PipelineStep, StepResult


class ApplyMappingStep(PipelineStep):
    """Apply source-to-canonical field mappings and transformations."""

    def __init__(self, mapping_name: str):
        self._mapping_name = mapping_name

    @property
    def name(self) -> str:
        return f"transform_{self._mapping_name}"

    def execute(self, context: PipelineContext) -> StepResult:
        result = StepResult(step_name=self.name)

        # Use bronze rows if available, otherwise extracted rows
        rows = context.data.get("bronze_rows") or context.data.get(
            "extracted_rows", []
        )
        if not rows:
            result.status = "skipped"
            result.error_message = "No rows to transform"
            return result

        try:
            mapping_def = load_mapping(self._mapping_name)
        except (MappingValidationError, Exception) as e:
            result.status = "failed"
            result.error_message = f"Failed to load mapping: {e}"
            return result

        transformed_rows = []
        errors = 0
        for row in rows:
            try:
                transformed = apply_field_mappings(row, mapping_def.field_mappings)
                transformed_rows.append(transformed)
            except TransformationError as e:
                errors += 1
                context.log.warning(
                    "Transform error",
                    row=row,
                    error=str(e),
                )

        context.data["transformed_rows"] = transformed_rows
        result.metrics.rows_transformed = len(transformed_rows)
        result.metrics.errors = errors

        context.log.info(
            "Transform complete",
            rows=len(transformed_rows),
            errors=errors,
        )

        return result
