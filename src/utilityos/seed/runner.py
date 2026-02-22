"""Seed data runner — loads CSV seed data through bronze → silver → gold."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from uuid import uuid4

from sqlalchemy import Column, Engine, MetaData, Table, insert, select, text

from utilityos.codegen.ddl_generator import generate_table
from utilityos.codegen.layer_generator import (
    generate_bronze_table,
    generate_gold_dimension_table,
    generate_gold_fact_table,
)
from utilityos.common.logging import get_logger
from utilityos.common.types import DataType, SCDType
from utilityos.db.schemas import create_schemas
from utilityos.models.loader import load_all_entities, load_common_definitions
from utilityos.models.schema import CommonDefinitions, EntityDefinition

_SEED_DATA_DIR = Path(__file__).parent.parent.parent.parent / "data" / "seed"

# Entity load order respecting FK dependencies
ENTITY_LOAD_ORDER = [
    "customer",
    "premise",
    "account",
    "service_point",
    "meter",
    "billing",
    "payment",
    "usage_monthly",
]

# Maps (entity_name, fk_attr_name) → (referenced_entity, csv_column_with_bk)
FK_RESOLUTION_MAP: dict[tuple[str, str], tuple[str, str]] = {
    ("account", "customer_sk"): ("customer", "customer_number"),
    ("service_point", "premise_sk"): ("premise", "premise_number"),
    ("meter", "service_point_sk"): ("service_point", "service_point_number"),
    ("billing", "account_sk"): ("account", "account_number"),
    ("payment", "account_sk"): ("account", "account_number"),
    ("usage_monthly", "service_point_sk"): ("service_point", "service_point_number"),
}


@dataclass
class EntitySeedResult:
    """Result of seeding a single entity."""

    entity_name: str
    bronze_rows: int = 0
    silver_rows: int = 0
    gold_rows: int = 0
    errors: list[str] = field(default_factory=list)


@dataclass
class SeedReport:
    """Overall seed execution report."""

    results: list[EntitySeedResult] = field(default_factory=list)
    schemas_created: list[str] = field(default_factory=list)
    tables_created: int = 0

    @property
    def total_bronze(self) -> int:
        return sum(r.bronze_rows for r in self.results)

    @property
    def total_silver(self) -> int:
        return sum(r.silver_rows for r in self.results)

    @property
    def total_gold(self) -> int:
        return sum(r.gold_rows for r in self.results)

    @property
    def success(self) -> bool:
        return all(len(r.errors) == 0 for r in self.results)


class SeedRunner:
    """Load seed CSV data through the full bronze → silver → gold pipeline."""

    def __init__(
        self,
        engine: Engine,
        seed_dir: Path | None = None,
        source_system: str = "seed",
    ):
        self.engine = engine
        self.seed_dir = seed_dir or _SEED_DATA_DIR
        self.source_system = source_system
        self.batch_id = uuid4()
        self.log = get_logger(component="seed_runner")

        # Load model definitions
        self.entities: dict[str, EntityDefinition] = {}
        self.common: CommonDefinitions | None = None

        # SK lookup caches: entity_name → {business_key_value → surrogate_key}
        self._sk_cache: dict[str, dict[str, int]] = {}

        # SQLAlchemy table objects by layer
        self._bronze_tables: dict[str, Table] = {}
        self._silver_tables: dict[str, Table] = {}
        self._gold_tables: dict[str, Table] = {}

    def run(self, entities: list[str] | None = None) -> SeedReport:
        """Run the full seed pipeline."""
        report = SeedReport()

        # Load model definitions
        all_entities = load_all_entities()
        self.entities = {e.entity.name: e for e in all_entities}
        self.common = load_common_definitions()

        entity_list = entities or ENTITY_LOAD_ORDER

        # 1. Create schemas
        self.log.info("Creating database schemas")
        report.schemas_created = create_schemas(self.engine)

        # 2. Generate and create tables
        self.log.info("Generating and creating tables")
        self._create_tables(entity_list)
        report.tables_created = (
            len(self._bronze_tables)
            + len(self._silver_tables)
            + len(self._gold_tables)
        )
        self.log.info(
            "Tables created",
            bronze=len(self._bronze_tables),
            silver=len(self._silver_tables),
            gold=len(self._gold_tables),
        )

        # 3. Load each entity in dependency order
        for entity_name in entity_list:
            if entity_name not in self.entities:
                self.log.warning("Entity not found, skipping", entity=entity_name)
                continue

            self.log.info("Loading entity", entity=entity_name)
            result = self._load_entity(entity_name)
            report.results.append(result)

            if result.errors:
                self.log.error(
                    "Entity load errors",
                    entity=entity_name,
                    errors=result.errors,
                )
            else:
                self.log.info(
                    "Entity loaded",
                    entity=entity_name,
                    bronze=result.bronze_rows,
                    silver=result.silver_rows,
                    gold=result.gold_rows,
                )

        return report

    def _create_tables(self, entity_names: list[str]) -> None:
        """Generate and create all tables for the specified entities."""
        bronze_meta = MetaData(schema="bronze")
        silver_meta = MetaData(schema="silver")
        gold_meta = MetaData(schema="gold")

        for name in entity_names:
            entity_def = self.entities.get(name)
            if entity_def is None:
                continue

            # Bronze
            bronze_table = generate_bronze_table(
                entity_def, bronze_meta, self.source_system
            )
            self._bronze_tables[name] = bronze_table

            # Silver
            silver_table = generate_table(entity_def, silver_meta, self.common)
            self._silver_tables[name] = silver_table

            # Gold
            if entity_def.gold_layer:
                if entity_def.gold_layer.dimension:
                    gold_table = generate_gold_dimension_table(
                        entity_def, gold_meta, self.common
                    )
                    if gold_table is not None:
                        self._gold_tables[name] = gold_table
                elif entity_def.gold_layer.fact:
                    gold_table = generate_gold_fact_table(
                        entity_def, gold_meta, self.common
                    )
                    if gold_table is not None:
                        self._gold_tables[name] = gold_table

        # Create all tables in the database
        bronze_meta.create_all(self.engine)
        silver_meta.create_all(self.engine)
        gold_meta.create_all(self.engine)

    def _load_entity(self, entity_name: str) -> EntitySeedResult:
        """Load a single entity through bronze → silver → gold."""
        result = EntitySeedResult(entity_name=entity_name)
        entity_def = self.entities[entity_name]

        # Determine CSV filename (handle irregular plurals)
        no_plural = {"usage_monthly", "billing"}
        csv_name = f"{entity_name}.csv" if entity_name in no_plural else f"{entity_name}s.csv"
        csv_path = self.seed_dir / csv_name
        if not csv_path.exists():
            result.errors.append(f"Seed file not found: {csv_path}")
            return result

        raw_rows = self._read_csv(csv_path)
        if not raw_rows:
            result.errors.append(f"No rows in seed file: {csv_path}")
            return result

        try:
            # Bronze load
            result.bronze_rows = self._load_bronze(entity_name, raw_rows)

            # Silver load
            silver_rows = self._prepare_silver_rows(entity_name, entity_def, raw_rows)
            result.silver_rows = self._load_silver(entity_name, silver_rows)

            # Build SK cache for FK resolution by downstream entities
            self._build_sk_cache(entity_name, entity_def)

            # Gold load
            if entity_name in self._gold_tables:
                result.gold_rows = self._load_gold(entity_name, entity_def)
        except Exception as e:
            result.errors.append(str(e))

        return result

    def _read_csv(self, path: Path) -> list[dict[str, str]]:
        """Read a CSV file and return rows as dicts."""
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    def _load_bronze(self, entity_name: str, rows: list[dict]) -> int:
        """Insert rows into the bronze table (all values as text)."""
        bronze_table = self._bronze_tables.get(entity_name)
        if bronze_table is None:
            return 0

        now = datetime.now(timezone.utc)
        col_names = {c.name for c in bronze_table.columns}
        bronze_rows = []

        for i, row in enumerate(rows):
            bronze_row: dict = {}
            for col_name in col_names:
                if col_name == "_row_id":
                    continue  # Auto-generated
                elif col_name == "_batch_id":
                    bronze_row[col_name] = self.batch_id
                elif col_name == "_ingested_at":
                    bronze_row[col_name] = now
                elif col_name == "_source_system":
                    bronze_row[col_name] = self.source_system
                elif col_name == "_source_file":
                    bronze_row[col_name] = str(self.seed_dir)
                elif col_name == "_row_number":
                    bronze_row[col_name] = i + 1
                elif col_name in row:
                    bronze_row[col_name] = row[col_name] if row[col_name] else None
            bronze_rows.append(bronze_row)

        with self.engine.begin() as conn:
            conn.execute(insert(bronze_table), bronze_rows)

        return len(bronze_rows)

    def _prepare_silver_rows(
        self,
        entity_name: str,
        entity_def: EntityDefinition,
        raw_rows: list[dict],
    ) -> list[dict]:
        """Prepare rows for silver table: type cast, resolve FKs, add SCD/audit columns."""
        now = datetime.now(timezone.utc)
        silver_rows = []

        for row in raw_rows:
            silver_row: dict = {}

            # Business keys
            for bk in entity_def.keys.business:
                value = row.get(bk.name, "")
                silver_row[bk.name] = self._cast_value(value, bk.data_type)

            # Attributes
            for attr in entity_def.attributes:
                fk_key = (entity_name, attr.name)
                if fk_key in FK_RESOLUTION_MAP:
                    # FK column — resolve business key → surrogate key
                    ref_entity, csv_bk_col = FK_RESOLUTION_MAP[fk_key]
                    bk_value = row.get(csv_bk_col, "")
                    silver_row[attr.name] = self._resolve_sk(ref_entity, bk_value)
                else:
                    raw_value = row.get(attr.name, "")
                    casted = self._cast_value(raw_value, attr.data_type)
                    # Apply default for non-nullable attrs missing from CSV
                    if casted is None and not attr.nullable and attr.default:
                        casted = self._cast_value(attr.default, attr.data_type)
                    silver_row[attr.name] = casted

            # SCD Type 2 columns
            if entity_def.entity.scd_type == SCDType.TYPE2:
                silver_row["effective_from"] = now
                silver_row["effective_to"] = None
                silver_row["is_current"] = True
                silver_row["version_number"] = 1

            # Audit columns
            if entity_def.entity.include_audit_columns:
                silver_row["created_at"] = now
                silver_row["updated_at"] = now
                silver_row["source_system"] = self.source_system
                silver_row["batch_id"] = self.batch_id

            silver_rows.append(silver_row)

        return silver_rows

    def _load_silver(self, entity_name: str, rows: list[dict]) -> int:
        """Insert rows into the silver table."""
        silver_table = self._silver_tables.get(entity_name)
        if silver_table is None or not rows:
            return 0

        with self.engine.begin() as conn:
            conn.execute(insert(silver_table), rows)

        return len(rows)

    def _build_sk_cache(
        self, entity_name: str, entity_def: EntityDefinition
    ) -> None:
        """Cache surrogate keys for FK resolution by downstream entities."""
        silver_table = self._silver_tables.get(entity_name)
        if silver_table is None:
            return

        sk_col = entity_def.keys.surrogate.name
        bk_cols = [bk.name for bk in entity_def.keys.business]
        if not bk_cols:
            return

        bk_col = bk_cols[0]  # Primary business key

        with self.engine.connect() as conn:
            result = conn.execute(
                select(silver_table.c[sk_col], silver_table.c[bk_col])
            )
            self._sk_cache[entity_name] = {
                str(row[1]): row[0] for row in result
            }

    def _resolve_sk(self, entity_name: str, business_key_value: str) -> int | None:
        """Resolve a business key to a surrogate key from the cache."""
        if not business_key_value:
            return None
        cache = self._sk_cache.get(entity_name, {})
        return cache.get(business_key_value)

    def _load_gold(self, entity_name: str, entity_def: EntityDefinition) -> int:
        """Copy silver data into the gold table."""
        gold_table = self._gold_tables.get(entity_name)
        silver_table = self._silver_tables.get(entity_name)

        if gold_table is None or silver_table is None:
            return 0

        # Get common column names between silver and gold
        gold_col_names = {c.name for c in gold_table.columns}
        silver_select_cols = [
            c for c in silver_table.columns if c.name in gold_col_names
        ]

        with self.engine.begin() as conn:
            rows = conn.execute(select(*silver_select_cols)).mappings().all()
            if rows:
                insert_rows = [
                    {k: v for k, v in dict(r).items() if k in gold_col_names}
                    for r in rows
                ]
                conn.execute(insert(gold_table), insert_rows)
            return len(rows)

    def _cast_value(self, value: str, data_type: DataType) -> object:
        """Cast a CSV string value to the appropriate Python type."""
        if value is None or value == "":
            return None

        try:
            if data_type in (DataType.VARCHAR, DataType.TEXT):
                return str(value)
            elif data_type in (DataType.INTEGER, DataType.SMALLINT):
                return int(value)
            elif data_type == DataType.BIGINT:
                return int(value)
            elif data_type == DataType.NUMERIC:
                return Decimal(value)
            elif data_type == DataType.BOOLEAN:
                return value.lower() in ("true", "1", "yes", "t")
            elif data_type == DataType.DATE:
                return date.fromisoformat(value)
            elif data_type in (DataType.TIMESTAMP, DataType.TIMESTAMP_TZ):
                return datetime.fromisoformat(value)
            elif data_type == DataType.UUID:
                from uuid import UUID

                return UUID(value)
            else:
                return str(value)
        except (ValueError, TypeError, InvalidOperation):
            return None
