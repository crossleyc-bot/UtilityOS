"""Gold layer building — dimension and fact table population."""

from __future__ import annotations

from utilityos.pipeline.context import PipelineContext
from utilityos.pipeline.step import PipelineStep, StepResult


class DimensionBuildStep(PipelineStep):
    """Build gold-layer dimension tables from silver data."""

    @property
    def name(self) -> str:
        return "gold_dimension_build"

    def execute(self, context: PipelineContext) -> StepResult:
        result = StepResult(step_name=self.name)

        rows = context.data.get("silver_rows", [])
        if not rows:
            result.status = "skipped"
            result.error_message = "No silver rows to build from"
            return result

        if context.dry_run:
            result.metrics.rows_loaded_gold = len(rows)
            context.log.info("Gold dimension build (dry run)", rows=len(rows))
            return result

        context.data["gold_rows"] = rows
        result.metrics.rows_loaded_gold = len(rows)

        context.log.info("Gold dimension build complete", rows=len(rows))
        return result


class FactBuildStep(PipelineStep):
    """Build gold-layer fact tables from silver data."""

    @property
    def name(self) -> str:
        return "gold_fact_build"

    def execute(self, context: PipelineContext) -> StepResult:
        result = StepResult(step_name=self.name)

        rows = context.data.get("silver_rows", [])
        if not rows:
            result.status = "skipped"
            result.error_message = "No silver rows to build from"
            return result

        if context.dry_run:
            result.metrics.rows_loaded_gold = len(rows)
            context.log.info("Gold fact build (dry run)", rows=len(rows))
            return result

        context.data["gold_rows"] = rows
        result.metrics.rows_loaded_gold = len(rows)

        context.log.info("Gold fact build complete", rows=len(rows))
        return result
