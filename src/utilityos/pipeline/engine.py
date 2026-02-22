"""Pipeline execution engine."""

from __future__ import annotations

from dataclasses import dataclass, field

from utilityos.common.datetime_utils import utc_now
from utilityos.common.exceptions import PipelineError, PipelineStepError
from utilityos.common.logging import get_logger
from utilityos.pipeline.context import PipelineContext
from utilityos.pipeline.step import PipelineStep, StepResult


@dataclass
class PipelineResult:
    """Overall result of a pipeline execution."""

    pipeline_name: str
    status: str = "success"  # success, failed
    step_results: list[StepResult] = field(default_factory=list)
    error_message: str | None = None

    @property
    def total_duration_seconds(self) -> float:
        return sum(
            sr.duration_seconds or 0.0
            for sr in self.step_results
        )


class Pipeline:
    """A named, ordered sequence of steps for processing utility data."""

    def __init__(
        self,
        name: str,
        source_system: str,
        target_entity: str,
        steps: list[PipelineStep],
        description: str = "",
    ):
        self.name = name
        self.source_system = source_system
        self.target_entity = target_entity
        self.steps = steps
        self.description = description

    def validate(self, context: PipelineContext) -> list[str]:
        """Validate all steps before execution."""
        errors: list[str] = []
        for step in self.steps:
            step_errors = step.validate(context)
            errors.extend(step_errors)
        return errors

    def run(self, context: PipelineContext) -> PipelineResult:
        """Execute all steps in sequence."""
        log = get_logger(pipeline=self.name, batch_id=str(context.batch_id))
        log.info("Pipeline started", steps=len(self.steps))

        result = PipelineResult(pipeline_name=self.name)

        # Validate before running
        validation_errors = self.validate(context)
        if validation_errors:
            result.status = "failed"
            result.error_message = (
                f"Validation failed: {'; '.join(validation_errors)}"
            )
            log.error("Pipeline validation failed", errors=validation_errors)
            return result

        for step in self.steps:
            log.info("Step starting", step=step.name)

            try:
                step_result = step.execute(context)
            except PipelineStepError as e:
                step_result = StepResult(
                    step_name=step.name,
                    status="failed",
                    error_message=str(e),
                )
            except Exception as e:
                step_result = StepResult(
                    step_name=step.name,
                    status="failed",
                    error_message=f"Unexpected error: {e}",
                )

            step_result.completed_at = utc_now()
            result.step_results.append(step_result)

            if step_result.failed:
                result.status = "failed"
                result.error_message = (
                    f"Step '{step.name}' failed: {step_result.error_message}"
                )
                log.error(
                    "Step failed",
                    step=step.name,
                    error=step_result.error_message,
                )
                break

            # Merge step metrics into context
            context.metrics.merge(step_result.metrics)
            log.info(
                "Step completed",
                step=step.name,
                duration=step_result.duration_seconds,
            )

        if result.status == "success":
            log.info(
                "Pipeline completed successfully",
                total_duration=result.total_duration_seconds,
            )

        return result
