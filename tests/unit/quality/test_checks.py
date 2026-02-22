"""Tests for data quality checks."""

from __future__ import annotations

from utilityos.common.types import QualityCheckStatus
from utilityos.quality.checks.drift_check import check_schema_drift
from utilityos.quality.checks.null_check import check_not_null, generate_null_check_sql
from utilityos.quality.checks.range_check import check_range
from utilityos.quality.checks.reconciliation_check import (
    check_row_count_reconciliation,
)
from utilityos.quality.checks.referential_check import generate_referential_check_sql
from utilityos.quality.checks.uniqueness_check import (
    check_uniqueness,
    generate_uniqueness_check_sql,
)


class TestNullCheck:
    def test_passes_with_no_nulls(self) -> None:
        result = check_not_null("customer", "name", total_rows=100, null_count=0)
        assert result.status == QualityCheckStatus.PASSED
        assert result.records_failed == 0

    def test_fails_with_nulls(self) -> None:
        result = check_not_null("customer", "name", total_rows=100, null_count=5)
        assert result.status == QualityCheckStatus.FAILED
        assert result.records_failed == 5
        assert result.failure_rate == 0.05

    def test_sql_generation(self) -> None:
        sql = generate_null_check_sql("customer", "name")
        assert "COUNT(*)" in sql
        assert "IS NULL" in sql
        assert "silver.customer" in sql


class TestUniquenessCheck:
    def test_passes_no_duplicates(self) -> None:
        result = check_uniqueness(
            "customer", ["customer_number"], total_rows=100, duplicate_count=0
        )
        assert result.status == QualityCheckStatus.PASSED

    def test_fails_with_duplicates(self) -> None:
        result = check_uniqueness(
            "customer", ["customer_number"], total_rows=100, duplicate_count=3
        )
        assert result.status == QualityCheckStatus.FAILED
        assert result.records_failed == 3

    def test_sql_generation_basic(self) -> None:
        sql = generate_uniqueness_check_sql("customer", ["customer_number"])
        assert "DISTINCT" in sql

    def test_sql_generation_scoped(self) -> None:
        sql = generate_uniqueness_check_sql(
            "customer", ["customer_number"], scope="current_records"
        )
        assert "is_current = TRUE" in sql


class TestRangeCheck:
    def test_passes_in_range(self) -> None:
        result = check_range(
            "usage", "consumption",
            total_rows=100, out_of_range_count=0,
            min_value=0.0, max_value=10000.0,
        )
        assert result.status == QualityCheckStatus.PASSED

    def test_fails_out_of_range(self) -> None:
        result = check_range(
            "usage", "consumption",
            total_rows=100, out_of_range_count=5,
            min_value=0.0,
        )
        assert result.status == QualityCheckStatus.FAILED


class TestReconciliationCheck:
    def test_matching_counts(self) -> None:
        result = check_row_count_reconciliation(
            "customer", "bronze", "silver", 1000, 1000
        )
        assert result.status == QualityCheckStatus.PASSED

    def test_mismatched_counts(self) -> None:
        result = check_row_count_reconciliation(
            "customer", "bronze", "silver", 1000, 900
        )
        assert result.status == QualityCheckStatus.FAILED
        assert result.records_failed == 100


class TestDriftCheck:
    def test_no_drift(self) -> None:
        expected = ["col_a", "col_b", "col_c"]
        actual = ["col_a", "col_b", "col_c"]
        result = check_schema_drift("customer", expected, actual)
        assert result.status == QualityCheckStatus.PASSED

    def test_missing_columns(self) -> None:
        expected = ["col_a", "col_b", "col_c"]
        actual = ["col_a", "col_b"]
        result = check_schema_drift("customer", expected, actual)
        assert result.status == QualityCheckStatus.FAILED
        assert result.details is not None
        assert "col_c" in result.details["missing_columns"]

    def test_extra_columns(self) -> None:
        expected = ["col_a", "col_b"]
        actual = ["col_a", "col_b", "col_extra"]
        result = check_schema_drift("customer", expected, actual)
        assert result.status == QualityCheckStatus.FAILED
        assert "col_extra" in result.details["extra_columns"]


class TestReferentialCheckSQL:
    def test_sql_generation(self) -> None:
        sql = generate_referential_check_sql(
            "account", "customer_sk", "customer", "customer_sk"
        )
        assert "LEFT JOIN" in sql
        assert "silver.customer" in sql
        assert "IS NULL" in sql
