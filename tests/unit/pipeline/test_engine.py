"""Tests for pipeline execution engine."""

from __future__ import annotations

from utilityos.pipeline.context import PipelineContext
from utilityos.pipeline.engine import Pipeline
from utilityos.pipeline.step import PipelineStep, StepResult


class MockSuccessStep(PipelineStep):
    @property
    def name(self) -> str:
        return "mock_success"

    def execute(self, context: PipelineContext) -> StepResult:
        result = StepResult(step_name=self.name)
        context.data["ran_success"] = True
        return result


class MockFailStep(PipelineStep):
    @property
    def name(self) -> str:
        return "mock_fail"

    def execute(self, context: PipelineContext) -> StepResult:
        result = StepResult(step_name=self.name, status="failed", error_message="test failure")
        return result


class MockCountStep(PipelineStep):
    @property
    def name(self) -> str:
        return "mock_count"

    def execute(self, context: PipelineContext) -> StepResult:
        count = context.data.get("step_count", 0) + 1
        context.data["step_count"] = count
        return StepResult(step_name=self.name)


class TestPipeline:
    def _make_context(self) -> PipelineContext:
        return PipelineContext(
            pipeline_name="test",
            source_system="test_source",
            target_entity="test_entity",
        )

    def test_successful_pipeline(self) -> None:
        pipeline = Pipeline(
            name="test",
            source_system="test",
            target_entity="entity",
            steps=[MockSuccessStep()],
        )
        ctx = self._make_context()
        result = pipeline.run(ctx)
        assert result.status == "success"
        assert ctx.data["ran_success"] is True
        assert len(result.step_results) == 1

    def test_failed_pipeline_stops(self) -> None:
        pipeline = Pipeline(
            name="test",
            source_system="test",
            target_entity="entity",
            steps=[MockSuccessStep(), MockFailStep(), MockSuccessStep()],
        )
        ctx = self._make_context()
        result = pipeline.run(ctx)
        assert result.status == "failed"
        # Should stop after the failing step
        assert len(result.step_results) == 2

    def test_multiple_steps_execute_in_order(self) -> None:
        pipeline = Pipeline(
            name="test",
            source_system="test",
            target_entity="entity",
            steps=[MockCountStep(), MockCountStep(), MockCountStep()],
        )
        ctx = self._make_context()
        result = pipeline.run(ctx)
        assert result.status == "success"
        assert ctx.data["step_count"] == 3

    def test_empty_pipeline(self) -> None:
        pipeline = Pipeline(
            name="test",
            source_system="test",
            target_entity="entity",
            steps=[],
        )
        ctx = self._make_context()
        result = pipeline.run(ctx)
        assert result.status == "success"
