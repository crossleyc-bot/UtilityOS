"""Base class for pipeline steps."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from utilityos.common.datetime_utils import utc_now
from utilityos.pipeline.context import PipelineContext, PipelineMetrics


@dataclass
class StepResult:
    """Result of a pipeline step execution."""

    step_name: str
    status: str = "success"  # success, failed, skipped
    metrics: PipelineMetrics = field(default_factory=PipelineMetrics)
    error_message: str | None = None
    started_at: datetime = field(default_factory=utc_now)
    completed_at: datetime | None = None

    @property
    def failed(self) -> bool:
        return self.status == "failed"

    @property
    def duration_seconds(self) -> float | None:
        if self.completed_at is None:
            return None
        return (self.completed_at - self.started_at).total_seconds()


class PipelineStep(ABC):
    """Abstract base class for pipeline steps."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this step."""

    @abstractmethod
    def execute(self, context: PipelineContext) -> StepResult:
        """Execute this pipeline step.

        Args:
            context: The pipeline context with runtime state.

        Returns:
            StepResult with status, metrics, and any error info.
        """

    def validate(self, context: PipelineContext) -> list[str]:
        """Validate that this step can be executed.

        Returns a list of validation error messages (empty if valid).
        """
        return []
