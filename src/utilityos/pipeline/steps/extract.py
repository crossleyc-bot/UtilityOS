"""Data extraction pipeline steps."""

from __future__ import annotations

from utilityos.common.exceptions import ExtractionError
from utilityos.pipeline.context import PipelineContext, PipelineMetrics
from utilityos.pipeline.sources.csv_source import CSVSource
from utilityos.pipeline.step import PipelineStep, StepResult


class CSVExtractStep(PipelineStep):
    """Extract data from CSV files."""

    def __init__(
        self,
        path_pattern: str,
        delimiter: str = ",",
        encoding: str = "utf-8",
    ):
        self._path_pattern = path_pattern
        self._delimiter = delimiter
        self._encoding = encoding

    @property
    def name(self) -> str:
        return "csv_extract"

    def execute(self, context: PipelineContext) -> StepResult:
        result = StepResult(step_name=self.name)

        try:
            source = CSVSource(
                path_pattern=self._path_pattern,
                delimiter=self._delimiter,
                encoding=self._encoding,
            )
            with source:
                rows = source.extract()

            context.data["extracted_rows"] = rows
            result.metrics.rows_extracted = len(rows)
            context.log.info(
                "CSV extraction complete",
                rows=len(rows),
                pattern=self._path_pattern,
            )
        except ExtractionError as e:
            result.status = "failed"
            result.error_message = str(e)

        return result

    def validate(self, context: PipelineContext) -> list[str]:
        errors = []
        if not self._path_pattern:
            errors.append("CSVExtractStep: path_pattern is required")
        return errors
