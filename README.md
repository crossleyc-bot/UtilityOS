# UtilityOS

A vertically integrated operational intelligence platform built for electric, water, wastewater, and municipal utilities.

## UtilityOS Data Fabric

The Data Fabric is the foundational data architecture engine that powers the UtilityOS platform. It provides:

- **Canonical Utility Data Model** — Pre-built, domain-driven entity definitions (Customer, Account, Meter, Billing, Usage, Assets, Outages, and more)
- **Automated Data Layer Generation** — Bronze (raw ingestion), Silver (standardized/conformed), Gold (facts & dimensions)
- **Source Mapping & Integration** — Field-level mapping, code normalization, unit conversion, identity resolution
- **Data Quality & Observability** — Null validation, referential integrity, duplicate detection, schema drift monitoring
- **SCD Type 2 Support** — Full slowly changing dimension history tracking with effective dating

## Quick Start

```bash
# Install dependencies
uv sync

# Validate canonical model definitions
uv run utilityos model validate

# List all entities in the canonical model
uv run utilityos model list

# Inspect a specific entity
uv run utilityos model inspect customer

# Generate DDL for all layers
uv run utilityos ddl generate --layer all

# View entity relationship graph
uv run utilityos model graph
```

## Project Structure

```
src/utilityos/
├── cli/          # Typer CLI commands
├── codegen/      # DDL generation, layer management, SCD automation
├── common/       # Shared types, exceptions, logging
├── config/       # Pydantic Settings configuration
├── db/           # SQLAlchemy engine, schema management
├── mapping/      # Source-to-canonical field mapping framework
├── models/       # Canonical data model (YAML definitions + Pydantic validation)
├── pipeline/     # Pipeline execution engine and steps
└── quality/      # Data quality check framework
```

## Canonical Data Model Entities

| Entity | Domain | SCD Type | Description |
|--------|--------|----------|-------------|
| Customer | Customer Management | 2 | Person or organization with utility relationship |
| Account | Customer Management | 2 | Utility billing account |
| Premise | Field Operations | 2 | Physical location/address served |
| Service Point | Field Operations | 2 | Point of service delivery |
| Meter | Metering Operations | 2 | Metering device |
| Device | Metering Operations | 1 | AMI/communication device |
| Billing | Revenue Operations | 0 | Bill/invoice |
| Charge | Revenue Operations | 0 | Individual charge line item |
| Payment | Revenue Operations | 0 | Payment transaction |
| Usage Monthly | Metering Operations | 0 | Monthly aggregated usage |
| Usage Interval | Metering Operations | 0 | Interval (15-min/hourly) usage |
| Work Order | Field Operations | 1 | Service work order |
| Asset | Asset Management | 2 | Infrastructure asset |
| Outage | Operations Center | 1 | Service outage event |

## Running Tests

```bash
# Run unit tests
uv run pytest

# Run with coverage
uv run pytest --cov=utilityos
```

## Tech Stack

- **Python 3.12+** with `uv` package management
- **PostgreSQL** with bronze/silver/gold schema layering
- **SQLAlchemy 2.0** (Core API) for metadata-driven DDL generation
- **Alembic** for schema migrations
- **Pydantic 2.0** for YAML validation and configuration
- **Typer** for CLI
- **structlog** for structured logging
