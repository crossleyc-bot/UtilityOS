"""Integration test fixtures — requires a running PostgreSQL instance."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import Engine, create_engine, text

from utilityos.db.schemas import create_schemas, drop_schemas


def _get_test_db_url() -> str:
    """Build the test database connection URL from environment variables."""
    host = os.environ.get("UTILITYOS_DB_HOST", "localhost")
    port = os.environ.get("UTILITYOS_DB_PORT", "5432")
    name = os.environ.get("UTILITYOS_DB_NAME", "utilityos_dev")
    user = os.environ.get("UTILITYOS_DB_USER", "utilityos")
    password = os.environ.get("UTILITYOS_DB_PASSWORD", "utilityos")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"


@pytest.fixture(scope="session")
def db_engine() -> Engine:
    """Create a SQLAlchemy engine for integration tests."""
    url = _get_test_db_url()
    engine = create_engine(url, echo=False, pool_pre_ping=True)

    # Verify connectivity
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))

    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_schemas(db_engine: Engine):
    """Drop and recreate schemas before each test for isolation."""
    drop_schemas(db_engine)
    create_schemas(db_engine)
    yield
    drop_schemas(db_engine)
