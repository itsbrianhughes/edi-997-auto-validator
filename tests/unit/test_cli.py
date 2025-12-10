"""Unit tests for CLI commands."""

from pathlib import Path

import pytest
from click.testing import CliRunner

from cli.main import cli


@pytest.fixture
def runner() -> CliRunner:
    """Click test runner fixture."""
    return CliRunner()


def test_cli_help(runner: CliRunner) -> None:
    """Test CLI help output."""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "EDI 997 Functional Acknowledgment Auto-Validator" in result.output
    assert "validate" in result.output
    assert "reconcile" in result.output


def test_cli_version(runner: CliRunner) -> None:
    """Test CLI version output."""
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_validate_command_help(runner: CliRunner) -> None:
    """Test validate command help."""
    result = runner.invoke(cli, ["validate", "--help"])
    assert result.exit_code == 0
    assert "Validate a 997 Functional Acknowledgment file" in result.output
    assert "--format" in result.output
    assert "--output" in result.output


def test_reconcile_command_help(runner: CliRunner) -> None:
    """Test reconcile command help."""
    result = runner.invoke(cli, ["reconcile", "--help"])
    assert result.exit_code == 0
    assert "Reconcile a 997 with outbound transactions" in result.output
    assert "--format" in result.output
    assert "--output" in result.output


def test_validate_command_missing_file(runner: CliRunner) -> None:
    """Test validate command with missing file."""
    result = runner.invoke(cli, ["validate", "nonexistent.997"])
    assert result.exit_code != 0
    assert "does not exist" in result.output.lower() or "error" in result.output.lower()


def test_validate_command_format_options(runner: CliRunner) -> None:
    """Test validate command format options exist."""
    result = runner.invoke(cli, ["validate", "--help"])
    assert result.exit_code == 0
    assert "--format" in result.output
    assert "json" in result.output.lower()
    assert "markdown" in result.output.lower()
    assert "both" in result.output.lower()


def test_validate_command_json_mode_options(runner: CliRunner) -> None:
    """Test validate command JSON mode options exist."""
    result = runner.invoke(cli, ["validate", "--help"])
    assert result.exit_code == 0
    assert "--json-mode" in result.output
    assert "full" in result.output.lower()
    assert "summary" in result.output.lower()
    assert "compact" in result.output.lower()


def test_reconcile_command_missing_files(runner: CliRunner) -> None:
    """Test reconcile command with missing files."""
    result = runner.invoke(
        cli, ["reconcile", "nonexistent.997", "nonexistent.json"]
    )
    assert result.exit_code != 0
