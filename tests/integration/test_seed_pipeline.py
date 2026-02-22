"""Integration tests for seed data pipeline — full bronze → silver → gold flow.

Requires a running PostgreSQL instance. Set UTILITYOS_DB_* environment variables
or use defaults (localhost:5432/utilityos_dev, user=utilityos, password=utilityos).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import Engine, text

pytestmark = pytest.mark.integration

from utilityos.codegen.ddl_generator import generate_table
from utilityos.codegen.layer_generator import (
    generate_bronze_table,
    generate_gold_dimension_table,
    generate_gold_fact_table,
)
from utilityos.models.loader import load_all_entities, load_common_definitions
from utilityos.models.registry import ModelRegistry
from utilityos.quality.engine import QualityEngine
from utilityos.seed.runner import ENTITY_LOAD_ORDER, SeedRunner

_SEED_DIR = Path(__file__).parent.parent.parent / "data" / "seed"

# Expected row counts per entity in the seed data
EXPECTED_COUNTS = {
    "customer": 10,
    "premise": 10,
    "account": 12,
    "service_point": 12,
    "meter": 10,
    "billing": 20,
    "payment": 15,
    "usage_monthly": 24,
}


@pytest.fixture
def seed_runner(db_engine: Engine) -> SeedRunner:
    """Create a SeedRunner instance for testing."""
    return SeedRunner(engine=db_engine, seed_dir=_SEED_DIR, source_system="seed")


# --- Schema and DDL tests ---


class TestSchemaCreation:
    """Test that database schemas are created correctly."""

    def test_schemas_exist(self, db_engine: Engine) -> None:
        """All four data layer schemas should exist."""
        with db_engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT schema_name FROM information_schema.schemata "
                    "WHERE schema_name IN ('bronze', 'silver', 'gold', 'meta')"
                )
            )
            schemas = sorted(row[0] for row in result)
        assert schemas == ["bronze", "gold", "meta", "silver"]

    def test_silver_table_creation(self, db_engine: Engine) -> None:
        """Silver tables should be created for all entities."""
        from sqlalchemy import MetaData

        entities = load_all_entities()
        common = load_common_definitions()
        silver_meta = MetaData(schema="silver")

        for entity_def in entities:
            generate_table(entity_def, silver_meta, common)

        silver_meta.create_all(db_engine)

        with db_engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'silver' ORDER BY table_name"
                )
            )
            tables = [row[0] for row in result]

        assert len(tables) >= 8
        assert "customer" in tables
        assert "account" in tables
        assert "billing" in tables


# --- Full pipeline tests ---


class TestSeedPipeline:
    """Test the full seed data pipeline: CSV → bronze → silver → gold."""

    def test_full_seed_load(self, seed_runner: SeedRunner) -> None:
        """Full seed load should succeed without errors."""
        report = seed_runner.run()

        assert report.success, f"Seed errors: {[(r.entity_name, r.errors) for r in report.results if r.errors]}"
        assert report.total_bronze > 0
        assert report.total_silver > 0
        assert report.total_gold > 0

    def test_bronze_row_counts(self, seed_runner: SeedRunner, db_engine: Engine) -> None:
        """Bronze tables should contain the expected number of rows."""
        seed_runner.run()

        with db_engine.connect() as conn:
            for entity_name, expected in EXPECTED_COUNTS.items():
                result = conn.execute(
                    text(f"SELECT COUNT(*) FROM bronze.seed_{entity_name}")
                )
                actual = result.scalar()
                assert actual == expected, (
                    f"Bronze {entity_name}: expected {expected}, got {actual}"
                )

    def test_silver_row_counts(self, seed_runner: SeedRunner, db_engine: Engine) -> None:
        """Silver tables should contain the expected number of rows."""
        seed_runner.run()

        with db_engine.connect() as conn:
            for entity_name, expected in EXPECTED_COUNTS.items():
                result = conn.execute(
                    text(f"SELECT COUNT(*) FROM silver.{entity_name}")
                )
                actual = result.scalar()
                assert actual == expected, (
                    f"Silver {entity_name}: expected {expected}, got {actual}"
                )

    def test_gold_row_counts(self, seed_runner: SeedRunner, db_engine: Engine) -> None:
        """Gold dimension and fact tables should contain rows."""
        seed_runner.run()

        with db_engine.connect() as conn:
            # Dimension tables
            for entity_name in ["customer", "premise", "account", "service_point", "meter"]:
                result = conn.execute(
                    text(f"SELECT COUNT(*) FROM gold.dim_{entity_name}")
                )
                actual = result.scalar()
                assert actual == EXPECTED_COUNTS[entity_name], (
                    f"Gold dim_{entity_name}: expected {EXPECTED_COUNTS[entity_name]}, got {actual}"
                )

            # Fact tables
            for entity_name in ["billing", "payment", "usage_monthly"]:
                result = conn.execute(
                    text(f"SELECT COUNT(*) FROM gold.fact_{entity_name}")
                )
                actual = result.scalar()
                assert actual == EXPECTED_COUNTS[entity_name], (
                    f"Gold fact_{entity_name}: expected {EXPECTED_COUNTS[entity_name]}, got {actual}"
                )


# --- FK resolution tests ---


class TestForeignKeyResolution:
    """Test that FK surrogate keys are correctly resolved."""

    def test_account_customer_sk(self, seed_runner: SeedRunner, db_engine: Engine) -> None:
        """Account.customer_sk should point to valid customer records."""
        seed_runner.run()

        with db_engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT COUNT(*) FROM silver.account a "
                    "JOIN silver.customer c ON a.customer_sk = c.customer_sk"
                )
            )
            joined_count = result.scalar()
            assert joined_count == 12, f"Expected 12 joined rows, got {joined_count}"

    def test_service_point_premise_sk(self, seed_runner: SeedRunner, db_engine: Engine) -> None:
        """ServicePoint.premise_sk should point to valid premise records."""
        seed_runner.run()

        with db_engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT COUNT(*) FROM silver.service_point sp "
                    "JOIN silver.premise p ON sp.premise_sk = p.premise_sk"
                )
            )
            joined_count = result.scalar()
            assert joined_count == 12, f"Expected 12 joined rows, got {joined_count}"

    def test_billing_account_sk(self, seed_runner: SeedRunner, db_engine: Engine) -> None:
        """Billing.account_sk should point to valid account records."""
        seed_runner.run()

        with db_engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT COUNT(*) FROM silver.billing b "
                    "JOIN silver.account a ON b.account_sk = a.account_sk"
                )
            )
            joined_count = result.scalar()
            assert joined_count == 20, f"Expected 20 joined rows, got {joined_count}"


# --- SCD Type 2 tests ---


class TestSCDType2:
    """Test SCD Type 2 columns are populated correctly."""

    def test_scd2_columns_present(self, seed_runner: SeedRunner, db_engine: Engine) -> None:
        """SCD2 entities should have is_current and version_number columns."""
        seed_runner.run()

        with db_engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT is_current, version_number, effective_from "
                    "FROM silver.customer LIMIT 1"
                )
            )
            row = result.fetchone()
            assert row is not None
            assert row[0] is True  # is_current
            assert row[1] == 1  # version_number
            assert row[2] is not None  # effective_from

    def test_all_customers_current(self, seed_runner: SeedRunner, db_engine: Engine) -> None:
        """Initial load: all customer records should be current."""
        seed_runner.run()

        with db_engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT COUNT(*) FROM silver.customer WHERE is_current = TRUE"
                )
            )
            assert result.scalar() == 10


# --- Data quality tests ---


class TestDataQuality:
    """Test in-memory quality checks against loaded data."""

    def test_customer_quality(self, seed_runner: SeedRunner, db_engine: Engine) -> None:
        """Customer data should pass quality checks."""
        seed_runner.run()

        # Load data from silver for in-memory quality checks
        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM silver.customer"))
            columns = result.keys()
            rows = [dict(zip(columns, row)) for row in result.fetchall()]

        entities = load_all_entities()
        common = load_common_definitions()
        registry = ModelRegistry()
        for entity_def in entities:
            registry.register(entity_def)

        engine = QualityEngine(registry)
        report = engine.validate_in_memory("customer", rows, "silver")

        assert report.pass_rate >= 0.8, (
            f"Customer quality pass rate too low: {report.pass_rate:.0%}"
        )

    def test_billing_quality(self, seed_runner: SeedRunner, db_engine: Engine) -> None:
        """Billing data should pass quality checks."""
        seed_runner.run()

        with db_engine.connect() as conn:
            result = conn.execute(text("SELECT * FROM silver.billing"))
            columns = result.keys()
            rows = [dict(zip(columns, row)) for row in result.fetchall()]

        entities = load_all_entities()
        registry = ModelRegistry()
        for entity_def in entities:
            registry.register(entity_def)

        engine = QualityEngine(registry)
        report = engine.validate_in_memory("billing", rows, "silver")

        assert report.pass_rate >= 0.8, (
            f"Billing quality pass rate too low: {report.pass_rate:.0%}"
        )


# --- Cross-layer consistency tests ---


class TestCrossLayerConsistency:
    """Test that data is consistent across bronze, silver, and gold layers."""

    def test_bronze_silver_counts_match(self, seed_runner: SeedRunner, db_engine: Engine) -> None:
        """Row counts should be the same in bronze and silver for each entity."""
        seed_runner.run()

        with db_engine.connect() as conn:
            for entity_name in EXPECTED_COUNTS:
                bronze = conn.execute(
                    text(f"SELECT COUNT(*) FROM bronze.seed_{entity_name}")
                ).scalar()
                silver = conn.execute(
                    text(f"SELECT COUNT(*) FROM silver.{entity_name}")
                ).scalar()
                assert bronze == silver, (
                    f"{entity_name}: bronze={bronze}, silver={silver}"
                )

    def test_silver_gold_counts_match(self, seed_runner: SeedRunner, db_engine: Engine) -> None:
        """Row counts should be the same in silver and gold for each entity."""
        report = seed_runner.run()

        dims = {"customer", "premise", "account", "service_point", "meter"}
        facts = {"billing", "payment", "usage_monthly"}

        with db_engine.connect() as conn:
            for entity_name in EXPECTED_COUNTS:
                silver = conn.execute(
                    text(f"SELECT COUNT(*) FROM silver.{entity_name}")
                ).scalar()

                if entity_name in dims:
                    gold_table = f"gold.dim_{entity_name}"
                else:
                    gold_table = f"gold.fact_{entity_name}"

                gold = conn.execute(
                    text(f"SELECT COUNT(*) FROM {gold_table}")
                ).scalar()

                assert silver == gold, (
                    f"{entity_name}: silver={silver}, gold={gold}"
                )

    def test_audit_columns_populated(self, seed_runner: SeedRunner, db_engine: Engine) -> None:
        """Audit columns should be populated in silver tables."""
        seed_runner.run()

        with db_engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT source_system, batch_id, created_at, updated_at "
                    "FROM silver.customer LIMIT 1"
                )
            )
            row = result.fetchone()
            assert row is not None
            assert row[0] == "seed"  # source_system
            assert row[1] is not None  # batch_id
            assert row[2] is not None  # created_at
            assert row[3] is not None  # updated_at
