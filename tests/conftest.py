"""Shared test fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def definitions_dir() -> Path:
    """Path to the YAML model definitions directory."""
    return Path(__file__).parent.parent / "src" / "utilityos" / "models" / "definitions"


@pytest.fixture
def sample_entity_yaml() -> str:
    """Minimal valid entity YAML for testing."""
    return """\
entity:
  name: test_entity
  display_name: "Test Entity"
  description: "A test entity for unit testing."
  domain: "testing"
  version: "1.0.0"
  scd_type: 2
  include_audit_columns: true

keys:
  surrogate:
    name: test_entity_sk
    data_type: bigint
    generated: "ALWAYS AS IDENTITY"
  business:
    - name: test_id
      data_type: varchar
      length: 50
      description: "Test business key"
      source_of_truth: true

attributes:
  - name: test_name
    data_type: varchar
    length: 100
    nullable: false
    description: "Test attribute"
  - name: test_value
    data_type: numeric
    precision: 12
    scale: 2
    nullable: true
"""
