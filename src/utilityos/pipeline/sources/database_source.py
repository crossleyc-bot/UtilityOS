"""Database data source connector using SQLAlchemy."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Engine, create_engine, text

from utilityos.common.exceptions import ExtractionError, SourceConnectionError
from utilityos.pipeline.sources.base import DataSource


class DatabaseSource(DataSource):
    """Extract data from a database via SQLAlchemy."""

    def __init__(
        self,
        connection_url: str | None = None,
        engine: Engine | None = None,
        query: str | None = None,
        table: str | None = None,
        schema: str | None = None,
    ):
        self._connection_url = connection_url
        self._engine = engine
        self._query = query
        self._table = table
        self._schema = schema
        self._owns_engine = False

    def connect(self) -> None:
        """Establish database connection."""
        if self._engine is None:
            if self._connection_url is None:
                raise SourceConnectionError(
                    "Either connection_url or engine must be provided"
                )
            try:
                self._engine = create_engine(self._connection_url)
                self._owns_engine = True
            except Exception as e:
                raise SourceConnectionError(
                    f"Failed to connect to database: {e}"
                ) from e

    def extract(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Execute the query and return results as dicts."""
        if self._engine is None:
            raise ExtractionError("Not connected. Call connect() first.")

        query = self._build_query()

        try:
            with self._engine.connect() as conn:
                result = conn.execute(text(query))
                columns = list(result.keys())
                return [dict(zip(columns, row)) for row in result]
        except Exception as e:
            raise ExtractionError(f"Query execution failed: {e}") from e

    def _build_query(self) -> str:
        """Build the extraction query."""
        if self._query:
            return self._query
        if self._table:
            table_ref = (
                f"{self._schema}.{self._table}"
                if self._schema
                else self._table
            )
            return f"SELECT * FROM {table_ref}"
        raise ExtractionError("Either query or table must be specified")

    def disconnect(self) -> None:
        """Close the database connection if we own it."""
        if self._owns_engine and self._engine is not None:
            self._engine.dispose()
            self._engine = None
