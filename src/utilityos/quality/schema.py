"""Pydantic models for quality rule definitions."""

from __future__ import annotations

from pydantic import BaseModel

from utilityos.common.types import QualityCheckStatus


class QualityCheckResult(BaseModel):
    """Result of a single quality check execution."""

    check_type: str
    check_name: str
    entity_name: str
    layer: str
    status: QualityCheckStatus
    records_checked: int = 0
    records_failed: int = 0
    failure_rate: float = 0.0
    message: str = ""
    details: dict | None = None

    @property
    def passed(self) -> bool:
        return self.status == QualityCheckStatus.PASSED


class QualityReport(BaseModel):
    """Aggregated quality check report."""

    entity_name: str | None = None
    layer: str = "silver"
    results: list[QualityCheckResult] = []

    @property
    def total_checks(self) -> int:
        return len(self.results)

    @property
    def passed_checks(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed_checks(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def pass_rate(self) -> float:
        if self.total_checks == 0:
            return 1.0
        return self.passed_checks / self.total_checks
