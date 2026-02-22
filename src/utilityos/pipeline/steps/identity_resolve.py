"""Identity resolution — cross-reference and deduplicate records."""

from __future__ import annotations

from typing import Any

from utilityos.pipeline.context import PipelineContext
from utilityos.pipeline.step import PipelineStep, StepResult


class IdentityResolveStep(PipelineStep):
    """Cross-reference records across source systems to detect duplicates."""

    def __init__(self, match_columns: list[str], fuzzy: bool = False):
        self._match_columns = match_columns
        self._fuzzy = fuzzy

    @property
    def name(self) -> str:
        return "identity_resolve"

    def execute(self, context: PipelineContext) -> StepResult:
        result = StepResult(step_name=self.name)

        rows = context.data.get("transformed_rows", [])
        if not rows:
            result.status = "skipped"
            return result

        # Exact match deduplication on match columns
        seen: dict[tuple, int] = {}
        deduplicated: list[dict[str, Any]] = []
        duplicates = 0

        for row in rows:
            key = tuple(row.get(col) for col in self._match_columns)
            if key in seen:
                duplicates += 1
            else:
                seen[key] = len(deduplicated)
                deduplicated.append(row)

        context.data["transformed_rows"] = deduplicated
        result.metrics.rows_transformed = len(deduplicated)

        context.log.info(
            "Identity resolution complete",
            input_rows=len(rows),
            output_rows=len(deduplicated),
            duplicates_removed=duplicates,
        )

        return result
