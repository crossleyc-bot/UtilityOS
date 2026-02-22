"""Bronze layer loading — raw ingestion into staging tables."""

from __future__ import annotations

from typing import Any

from utilityos.common.datetime_utils import utc_now
from utilityos.common.exceptions import LoadError
from utilityos.pipeline.context import PipelineContext
from utilityos.pipeline.step import PipelineStep, StepResult


class BronzeLoadStep(PipelineStep):
    """Load extracted data into the bronze staging layer.

    All values are stored as text. Adds metadata columns
    for lineage tracking.
    """

    @property
    def name(self) -> str:
        return "bronze_load"

    def execute(self, context: PipelineContext) -> StepResult:
        result = StepResult(step_name=self.name)

        rows = context.data.get("extracted_rows", [])
        if not rows:
            result.status = "skipped"
            result.error_message = "No rows to load"
            return result

        if context.dry_run:
            result.metrics.rows_loaded_bronze = len(rows)
            context.log.info("Bronze load (dry run)", rows=len(rows))
            return result

        try:
            # Tag rows with bronze metadata
            bronze_rows = self._prepare_bronze_rows(rows, context)
            context.data["bronze_rows"] = bronze_rows
            result.metrics.rows_loaded_bronze = len(bronze_rows)

            context.log.info("Bronze load complete", rows=len(bronze_rows))
        except Exception as e:
            result.status = "failed"
            result.error_message = f"Bronze load failed: {e}"

        return result

    def _prepare_bronze_rows(
        self,
        rows: list[dict[str, Any]],
        context: PipelineContext,
    ) -> list[dict[str, Any]]:
        """Add bronze metadata columns to each row."""
        now = utc_now()
        bronze_rows = []

        for i, row in enumerate(rows):
            bronze_row = {k: str(v) if v is not None else None for k, v in row.items()}
            bronze_row["_batch_id"] = str(context.batch_id)
            bronze_row["_ingested_at"] = now.isoformat()
            bronze_row["_source_system"] = context.source_system
            bronze_row["_row_number"] = i + 1
            bronze_rows.append(bronze_row)

        return bronze_rows
