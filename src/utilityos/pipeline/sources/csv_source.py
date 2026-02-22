"""CSV/flat file data source connector."""

from __future__ import annotations

import csv
from glob import glob
from pathlib import Path
from typing import Any

from utilityos.common.exceptions import ExtractionError
from utilityos.pipeline.sources.base import DataSource


class CSVSource(DataSource):
    """Extract data from CSV files."""

    def __init__(
        self,
        path_pattern: str,
        delimiter: str = ",",
        encoding: str = "utf-8",
        has_header: bool = True,
    ):
        self.path_pattern = path_pattern
        self.delimiter = delimiter
        self.encoding = encoding
        self.has_header = has_header
        self._files: list[str] = []

    def connect(self) -> None:
        """Discover files matching the path pattern."""
        self._files = sorted(glob(self.path_pattern))
        if not self._files:
            raise ExtractionError(
                f"No files found matching pattern: {self.path_pattern}"
            )

    def extract(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Read all matching CSV files and return rows as dicts."""
        all_rows: list[dict[str, Any]] = []

        for file_path in self._files:
            rows = self._read_file(file_path)
            # Tag each row with source file info
            for row in rows:
                row["_source_file"] = file_path
            all_rows.extend(rows)

        return all_rows

    def _read_file(self, file_path: str) -> list[dict[str, Any]]:
        """Read a single CSV file."""
        try:
            path = Path(file_path)
            with open(path, newline="", encoding=self.encoding) as f:
                if self.has_header:
                    reader = csv.DictReader(f, delimiter=self.delimiter)
                    return list(reader)
                else:
                    reader = csv.reader(f, delimiter=self.delimiter)
                    rows = list(reader)
                    # Use column indices as keys
                    return [
                        {str(i): v for i, v in enumerate(row)}
                        for row in rows
                    ]
        except Exception as e:
            raise ExtractionError(
                f"Failed to read CSV file '{file_path}': {e}"
            ) from e

    def disconnect(self) -> None:
        """No cleanup needed for file sources."""
        self._files = []
