"""Abstract base class for data source connectors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class DataSource(ABC):
    """Abstract interface for data source connectors."""

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to the data source."""

    @abstractmethod
    def extract(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Extract data from the source.

        Returns a list of dictionaries (rows).
        """

    @abstractmethod
    def disconnect(self) -> None:
        """Close the data source connection."""

    def __enter__(self) -> DataSource:
        self.connect()
        return self

    def __exit__(self, *args: object) -> None:
        self.disconnect()
