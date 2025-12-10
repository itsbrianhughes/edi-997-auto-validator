"""Structured logging with JSON output and colorized console support."""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

from src.models.config_schemas import AppConfig, LogFormat, LogLevel

# Custom theme for rich console
CUSTOM_THEME = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "bold red",
        "critical": "bold white on red",
        "success": "bold green",
    }
)

# Global console instance
console = Console(theme=CUSTOM_THEME)


class MaxLevelFilter(logging.Filter):
    """Filter to restrict log records to a maximum level."""

    def __init__(self, level: str) -> None:
        """Initialize filter with maximum level.

        Args:
            level: Maximum log level (e.g., 'INFO')
        """
        super().__init__()
        self.max_level = getattr(logging, level)

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log records.

        Args:
            record: Log record to filter

        Returns:
            True if record should be logged, False otherwise
        """
        return record.levelno <= self.max_level


def setup_logging(
    log_level: LogLevel = LogLevel.INFO,
    log_format: LogFormat = LogFormat.JSON,
    enable_colors: bool = True,
    enable_file_logging: bool = True,
    log_file_path: Optional[Path] = None,
) -> None:
    """Configure structured logging with optional colorized console output.

    Args:
        log_level: Minimum logging level
        log_format: Log format (json, simple, detailed)
        enable_colors: Enable colorized console output with Rich
        enable_file_logging: Enable file logging
        log_file_path: Path to log file (default: logs/validator.log)
    """
    # Create logs directory if it doesn't exist
    if enable_file_logging:
        log_path = log_file_path or Path("logs/validator.log")
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure standard library logging
    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(funcName)s %(lineno)d %(message)s",
            },
            "simple": {
                "format": "%(message)s",
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {},
        "root": {
            "level": log_level.value,
            "handlers": [],
        },
    }

    # Add console handler
    if enable_colors and log_format != LogFormat.JSON:
        # Use Rich handler for colorized output
        rich_handler = RichHandler(
            console=console,
            rich_tracebacks=True,
            tracebacks_show_locals=True,
            markup=True,
        )
        rich_handler.setLevel(getattr(logging, log_level.value))
        logging.root.addHandler(rich_handler)
    else:
        # Use standard stream handler
        logging_config["handlers"]["console"] = {
            "class": "logging.StreamHandler",
            "level": log_level.value,
            "formatter": log_format.value,
            "stream": "ext://sys.stdout",
        }
        logging_config["root"]["handlers"].append("console")

    # Add file handler
    if enable_file_logging:
        log_path = log_file_path or Path("logs/validator.log")
        logging_config["handlers"]["file_json"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "json",
            "filename": str(log_path),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8",
        }
        logging_config["root"]["handlers"].append("file_json")

    # Configure logging if not using Rich exclusively
    if not (enable_colors and log_format != LogFormat.JSON):
        logging.config.dictConfig(logging_config)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a context-aware logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Structured logger instance with context binding support

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("parsing_started", file="997.edi", segments=42)
        >>> logger = logger.bind(transaction_id="12345")
        >>> logger.info("transaction_processed")  # Includes transaction_id in context
    """
    return structlog.get_logger(name)


def log_exception(
    logger: structlog.BoundLogger,
    message: str,
    exc: Exception,
    **context: Any,
) -> None:
    """Log an exception with full traceback and context.

    Args:
        logger: Logger instance
        message: Error message
        exc: Exception to log
        **context: Additional context to include in log
    """
    logger.exception(
        message,
        exc_info=exc,
        exception_type=type(exc).__name__,
        exception_message=str(exc),
        **context,
    )


def log_operation_start(
    logger: structlog.BoundLogger,
    operation: str,
    **context: Any,
) -> None:
    """Log the start of an operation.

    Args:
        logger: Logger instance
        operation: Operation name
        **context: Additional context
    """
    logger.info(f"{operation}_started", operation=operation, **context)


def log_operation_complete(
    logger: structlog.BoundLogger,
    operation: str,
    duration_seconds: Optional[float] = None,
    **context: Any,
) -> None:
    """Log the completion of an operation.

    Args:
        logger: Logger instance
        operation: Operation name
        duration_seconds: Operation duration
        **context: Additional context
    """
    log_data = {"operation": operation, **context}
    if duration_seconds is not None:
        log_data["duration_seconds"] = round(duration_seconds, 3)

    logger.info(f"{operation}_completed", **log_data)


def log_operation_failed(
    logger: structlog.BoundLogger,
    operation: str,
    error: str,
    **context: Any,
) -> None:
    """Log a failed operation.

    Args:
        logger: Logger instance
        operation: Operation name
        error: Error description
        **context: Additional context
    """
    logger.error(
        f"{operation}_failed",
        operation=operation,
        error=error,
        **context,
    )


# Convenience function to log structured data
def log_structured(
    logger: structlog.BoundLogger,
    level: str,
    event: str,
    **data: Any,
) -> None:
    """Log structured data at specified level.

    Args:
        logger: Logger instance
        level: Log level (debug, info, warning, error, critical)
        event: Event name
        **data: Structured data to log
    """
    log_method = getattr(logger, level.lower())
    log_method(event, **data)
