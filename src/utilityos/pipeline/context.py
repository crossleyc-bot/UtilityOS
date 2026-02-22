"""Pipeline execution context — runtime state passed between steps."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import structlog
from sqlalchemy import Engine

from utilityos.common.datetime_utils import utc_now
from utilityos.config.settings import Settings


@dataclass
class PipelineMetrics:
    """Metrics collected during pipeline execution."""

    rows_extracted: int = 0
    rows_loaded_bronze: int = 0
    rows_transformed: int = 0
    rows_loaded_silver: int = 0
    rows_inserted: int = 0
    rows_updated: int = 0
    rows_unchanged: int = 0
    rows_loaded_gold: int = 0
    errors: int = 0
    step_durations: dict[str, float] = field(default_factory=dict)

    def merge(self, other: PipelineMetrics) -> None:
        """Merge another PipelineMetrics into this one."""
        self.rows_extracted += other.rows_extracted
        self.rows_loaded_bronze += other.rows_loaded_bronze
        self.rows_transformed += other.rows_transformed
        self.rows_loaded_silver += other.rows_loaded_silver
        self.rows_inserted += other.rows_inserted
        self.rows_updated += other.rows_updated
        self.rows_unchanged += other.rows_unchanged
        self.rows_loaded_gold += other.rows_loaded_gold
        self.errors += other.errors
        self.step_durations.update(other.step_durations)


@dataclass
class PipelineContext:
    """Runtime context passed through pipeline steps."""

    pipeline_name: str
    source_system: str
    target_entity: str
    db_engine: Engine | None = None
    config: Settings | None = None
    batch_id: UUID = field(default_factory=uuid4)
    start_time: datetime = field(default_factory=utc_now)
    log: Any = field(default_factory=lambda: structlog.get_logger())
    metrics: PipelineMetrics = field(default_factory=PipelineMetrics)
    data: dict[str, Any] = field(default_factory=dict)
    dry_run: bool = False
