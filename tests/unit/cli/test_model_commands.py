"""Tests for CLI model commands."""

from __future__ import annotations

from typer.testing import CliRunner

from utilityos.cli.app import app

runner = CliRunner()


class TestModelCLI:
    def test_model_list(self) -> None:
        result = runner.invoke(app, ["model", "list"])
        # Should succeed and show a table
        assert result.exit_code == 0

    def test_model_validate(self) -> None:
        result = runner.invoke(app, ["model", "validate"])
        # Should succeed if YAML files are valid
        assert result.exit_code == 0

    def test_model_inspect_nonexistent(self) -> None:
        result = runner.invoke(app, ["model", "inspect", "nonexistent_xyz"])
        assert result.exit_code != 0

    def test_model_graph(self) -> None:
        result = runner.invoke(app, ["model", "graph"])
        assert result.exit_code == 0
