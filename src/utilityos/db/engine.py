"""SQLAlchemy engine and session factory."""

from __future__ import annotations

from sqlalchemy import Engine, create_engine

from utilityos.config.settings import Settings


def create_db_engine(settings: Settings) -> Engine:
    """Create a SQLAlchemy engine from application settings."""
    return create_engine(
        settings.db.url,
        echo=settings.environment == "development",
        pool_pre_ping=True,
    )
