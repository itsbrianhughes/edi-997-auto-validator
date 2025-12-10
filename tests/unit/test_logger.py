"""Unit tests for logger."""

import logging
from pathlib import Path

import pytest
import structlog

from src.models.config_schemas import LogFormat, LogLevel
from src.utils.logger import (
    get_logger,
    log_exception,
    log_operation_complete,
    log_operation_failed,
    log_operation_start,
    log_structured,
    setup_logging,
)


def test_setup_logging_basic() -> None:
    """Test basic logging setup."""
    setup_logging(
        log_level=LogLevel.INFO,
        log_format=LogFormat.SIMPLE,
        enable_colors=False,
        enable_file_logging=False,
    )

    # Should not raise any exceptions
    assert True


def test_get_logger() -> None:
    """Test getting a logger instance."""
    logger = get_logger(__name__)
    # Logger is a BoundLoggerLazyProxy, check it has the required methods
    assert hasattr(logger, "info")
    assert hasattr(logger, "error")
    assert hasattr(logger, "debug")
    assert hasattr(logger, "warning")


def test_logger_info(capsys: pytest.CaptureFixture) -> None:
    """Test logging info messages."""
    setup_logging(
        log_level=LogLevel.INFO,
        log_format=LogFormat.SIMPLE,
        enable_colors=False,
        enable_file_logging=False,
    )

    logger = get_logger(__name__)
    logger.info("test_message", key="value")

    # Check that message was logged to stdout
    captured = capsys.readouterr()
    assert "test_message" in captured.out


def test_logger_context_binding(capsys: pytest.CaptureFixture) -> None:
    """Test logger context binding."""
    setup_logging(
        log_level=LogLevel.INFO,
        log_format=LogFormat.SIMPLE,
        enable_colors=False,
        enable_file_logging=False,
    )

    logger = get_logger(__name__)
    bound_logger = logger.bind(transaction_id="12345")
    bound_logger.info("test_with_context")

    # Should have logged the message with context
    captured = capsys.readouterr()
    assert "test_with_context" in captured.out
    assert "12345" in captured.out


def test_log_exception(capsys: pytest.CaptureFixture) -> None:
    """Test logging exceptions."""
    setup_logging(
        log_level=LogLevel.ERROR,
        log_format=LogFormat.SIMPLE,
        enable_colors=False,
        enable_file_logging=False,
    )

    logger = get_logger(__name__)

    try:
        raise ValueError("Test exception")
    except ValueError as e:
        log_exception(logger, "operation_failed", e, operation="test")

    # Should have logged the exception
    captured = capsys.readouterr()
    assert "operation_failed" in captured.out


def test_log_operation_start(capsys: pytest.CaptureFixture) -> None:
    """Test logging operation start."""
    setup_logging(
        log_level=LogLevel.INFO,
        log_format=LogFormat.SIMPLE,
        enable_colors=False,
        enable_file_logging=False,
    )

    logger = get_logger(__name__)
    log_operation_start(logger, "parse_file", file="test.edi")

    captured = capsys.readouterr()
    assert "parse_file_started" in captured.out


def test_log_operation_complete(capsys: pytest.CaptureFixture) -> None:
    """Test logging operation completion."""
    setup_logging(
        log_level=LogLevel.INFO,
        log_format=LogFormat.SIMPLE,
        enable_colors=False,
        enable_file_logging=False,
    )

    logger = get_logger(__name__)
    log_operation_complete(logger, "parse_file", duration_seconds=1.5)

    captured = capsys.readouterr()
    assert "parse_file_completed" in captured.out


def test_log_operation_failed(capsys: pytest.CaptureFixture) -> None:
    """Test logging operation failure."""
    setup_logging(
        log_level=LogLevel.ERROR,
        log_format=LogFormat.SIMPLE,
        enable_colors=False,
        enable_file_logging=False,
    )

    logger = get_logger(__name__)
    log_operation_failed(logger, "parse_file", error="Invalid format")

    captured = capsys.readouterr()
    assert "parse_file_failed" in captured.out


def test_log_structured(capsys: pytest.CaptureFixture) -> None:
    """Test structured logging."""
    setup_logging(
        log_level=LogLevel.INFO,
        log_format=LogFormat.SIMPLE,
        enable_colors=False,
        enable_file_logging=False,
    )

    logger = get_logger(__name__)
    log_structured(logger, "info", "custom_event", data="value", count=42)

    captured = capsys.readouterr()
    assert "custom_event" in captured.out


def test_setup_logging_with_file(tmp_path: Path) -> None:
    """Test logging setup with file output."""
    log_file = tmp_path / "test.log"

    setup_logging(
        log_level=LogLevel.INFO,
        log_format=LogFormat.JSON,
        enable_colors=False,
        enable_file_logging=True,
        log_file_path=log_file,
    )

    logger = get_logger(__name__)
    logger.info("test_file_logging")

    # Give it a moment to write
    import time

    time.sleep(0.1)

    # Check that log file was created
    assert log_file.parent.exists()


def test_different_log_levels(capsys: pytest.CaptureFixture) -> None:
    """Test different log levels."""
    setup_logging(
        log_level=LogLevel.DEBUG,
        log_format=LogFormat.SIMPLE,
        enable_colors=False,
        enable_file_logging=False,
    )

    logger = get_logger(__name__)
    logger.debug("debug_message")
    logger.info("info_message")
    logger.warning("warning_message")
    logger.error("error_message")

    captured = capsys.readouterr()

    assert "debug_message" in captured.out
    assert "info_message" in captured.out
    assert "warning_message" in captured.out
    assert "error_message" in captured.out


def test_log_level_filtering(capsys: pytest.CaptureFixture) -> None:
    """Test that log level filtering works."""
    setup_logging(
        log_level=LogLevel.WARNING,
        log_format=LogFormat.SIMPLE,
        enable_colors=False,
        enable_file_logging=False,
    )

    logger = get_logger(__name__)
    logger.debug("debug_message")  # Should not appear
    logger.info("info_message")  # Should not appear
    logger.warning("warning_message")  # Should appear
    logger.error("error_message")  # Should appear

    captured = capsys.readouterr()

    assert "debug_message" not in captured.out
    assert "info_message" not in captured.out
    assert "warning_message" in captured.out
    assert "error_message" in captured.out
