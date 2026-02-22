"""Pipeline registry for discovering and listing available pipelines."""

from __future__ import annotations

from utilityos.common.exceptions import PipelineError
from utilityos.pipeline.engine import Pipeline


class PipelineRegistry:
    """Registry of available pipelines."""

    def __init__(self) -> None:
        self._pipelines: dict[str, Pipeline] = {}

    def register(self, pipeline: Pipeline) -> None:
        """Register a pipeline."""
        self._pipelines[pipeline.name] = pipeline

    def get(self, name: str) -> Pipeline:
        """Get a pipeline by name."""
        if name not in self._pipelines:
            raise PipelineError(
                f"Pipeline '{name}' not found. "
                f"Available: {', '.join(sorted(self._pipelines.keys()))}"
            )
        return self._pipelines[name]

    def list_pipelines(self) -> list[str]:
        """List all registered pipeline names."""
        return sorted(self._pipelines.keys())

    def __len__(self) -> int:
        return len(self._pipelines)

    def __contains__(self, name: str) -> bool:
        return name in self._pipelines
