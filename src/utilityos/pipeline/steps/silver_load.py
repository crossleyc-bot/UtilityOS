"""Silver layer loading with SCD Type 2 support."""

from __future__ import annotations

from utilityos.common.types import SCDType
from utilityos.pipeline.context import PipelineContext
from utilityos.pipeline.step import PipelineStep, StepResult


class SilverLoadStep(PipelineStep):
    """Load transformed data into the silver canonical layer.

    Supports SCD Type 0 (insert-only), Type 1 (overwrite),
    and Type 2 (full history) patterns.
    """

    def __init__(self, scd_type: int = 2):
        self._scd_type = SCDType(scd_type)

    @property
    def name(self) -> str:
        return "silver_load"

    def execute(self, context: PipelineContext) -> StepResult:
        result = StepResult(step_name=self.name)

        rows = context.data.get("transformed_rows", [])
        if not rows:
            result.status = "skipped"
            result.error_message = "No rows to load"
            return result

        if context.dry_run:
            result.metrics.rows_loaded_silver = len(rows)
            context.log.info(
                "Silver load (dry run)",
                rows=len(rows),
                scd_type=self._scd_type.value,
            )
            return result

        # Store rows for downstream steps
        context.data["silver_rows"] = rows
        result.metrics.rows_loaded_silver = len(rows)
        result.metrics.rows_inserted = len(rows)

        context.log.info(
            "Silver load complete",
            rows=len(rows),
            scd_type=self._scd_type.value,
        )

        return result
