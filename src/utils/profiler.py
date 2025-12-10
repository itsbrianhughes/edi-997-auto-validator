"""Performance profiling utilities for measuring operation timing."""

import functools
import time
from typing import Any, Callable, Dict, Optional, TypeVar, cast

import structlog

# Type variable for generic function
F = TypeVar("F", bound=Callable[..., Any])

# Global profiling state
_profiling_enabled = False
_slow_threshold_seconds = 1.0
_profile_stats: Dict[str, Dict[str, Any]] = {}

logger = structlog.get_logger(__name__)


def enable_profiling(slow_threshold: float = 1.0) -> None:
    """Enable performance profiling globally.

    Args:
        slow_threshold: Threshold in seconds for logging slow operations
    """
    global _profiling_enabled, _slow_threshold_seconds
    _profiling_enabled = True
    _slow_threshold_seconds = slow_threshold
    logger.info("profiling_enabled", slow_threshold_seconds=slow_threshold)


def disable_profiling() -> None:
    """Disable performance profiling globally."""
    global _profiling_enabled
    _profiling_enabled = False
    logger.info("profiling_disabled")


def is_profiling_enabled() -> bool:
    """Check if profiling is enabled.

    Returns:
        True if profiling is enabled
    """
    return _profiling_enabled


def get_profile_stats() -> Dict[str, Dict[str, Any]]:
    """Get accumulated profiling statistics.

    Returns:
        Dictionary mapping operation names to their statistics
    """
    return _profile_stats.copy()


def clear_profile_stats() -> None:
    """Clear accumulated profiling statistics."""
    global _profile_stats
    _profile_stats = {}
    logger.info("profile_stats_cleared")


def _update_stats(operation: str, duration: float) -> None:
    """Update profiling statistics for an operation.

    Args:
        operation: Operation name
        duration: Duration in seconds
    """
    if operation not in _profile_stats:
        _profile_stats[operation] = {
            "count": 0,
            "total_seconds": 0.0,
            "min_seconds": float("inf"),
            "max_seconds": 0.0,
            "avg_seconds": 0.0,
        }

    stats = _profile_stats[operation]
    stats["count"] += 1
    stats["total_seconds"] += duration
    stats["min_seconds"] = min(stats["min_seconds"], duration)
    stats["max_seconds"] = max(stats["max_seconds"], duration)
    stats["avg_seconds"] = stats["total_seconds"] / stats["count"]


def profile(
    operation: Optional[str] = None,
    log_level: str = "info",
    include_args: bool = False,
) -> Callable[[F], F]:
    """Decorator to profile function execution time.

    Args:
        operation: Operation name (defaults to function name)
        log_level: Log level for profiling info (debug, info, warning)
        include_args: Include function arguments in log

    Returns:
        Decorated function

    Example:
        >>> @profile(operation="parse_997")
        ... def parse_file(filename):
        ...     # parsing logic
        ...     pass
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # If profiling disabled, just call the function
            if not _profiling_enabled:
                return func(*args, **kwargs)

            # Determine operation name
            op_name = operation or func.__name__

            # Start timing
            start_time = time.perf_counter()

            try:
                # Execute function
                result = func(*args, **kwargs)

                # Calculate duration
                duration = time.perf_counter() - start_time

                # Update statistics
                _update_stats(op_name, duration)

                # Log if slow operation
                if duration >= _slow_threshold_seconds:
                    log_data: Dict[str, Any] = {
                        "operation": op_name,
                        "duration_seconds": round(duration, 3),
                        "slow_operation": True,
                    }

                    if include_args:
                        log_data["args"] = str(args)[:100]  # Truncate long args
                        log_data["kwargs"] = {k: str(v)[:100] for k, v in kwargs.items()}

                    log_method = getattr(logger, log_level)
                    log_method("operation_completed", **log_data)

                return result

            except Exception as e:
                # Log failed operation
                duration = time.perf_counter() - start_time
                logger.error(
                    "operation_failed",
                    operation=op_name,
                    duration_seconds=round(duration, 3),
                    error=str(e),
                )
                raise

        return cast(F, wrapper)

    return decorator


class ProfileContext:
    """Context manager for profiling code blocks.

    Example:
        >>> with ProfileContext("parse_segments"):
        ...     # code to profile
        ...     pass
    """

    def __init__(self, operation: str, log_level: str = "info") -> None:
        """Initialize profile context.

        Args:
            operation: Operation name
            log_level: Log level for profiling info
        """
        self.operation = operation
        self.log_level = log_level
        self.start_time: Optional[float] = None
        self.duration: Optional[float] = None

    def __enter__(self) -> "ProfileContext":
        """Enter context and start timing."""
        if _profiling_enabled:
            self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context and log timing."""
        if not _profiling_enabled or self.start_time is None:
            return

        self.duration = time.perf_counter() - self.start_time

        # Update statistics
        _update_stats(self.operation, self.duration)

        # Log if slow operation or if error occurred
        if self.duration >= _slow_threshold_seconds or exc_type is not None:
            log_data: Dict[str, Any] = {
                "operation": self.operation,
                "duration_seconds": round(self.duration, 3),
            }

            if self.duration >= _slow_threshold_seconds:
                log_data["slow_operation"] = True

            if exc_type is not None:
                log_data["error"] = str(exc_val)
                logger.error("operation_failed", **log_data)
            else:
                log_method = getattr(logger, self.log_level)
                log_method("operation_completed", **log_data)


def profile_block(operation: str) -> ProfileContext:
    """Create a profiling context manager.

    Args:
        operation: Operation name

    Returns:
        ProfileContext instance

    Example:
        >>> with profile_block("parse_997"):
        ...     # code to profile
        ...     pass
    """
    return ProfileContext(operation)


def get_operation_stats(operation: str) -> Optional[Dict[str, Any]]:
    """Get profiling statistics for a specific operation.

    Args:
        operation: Operation name

    Returns:
        Statistics dictionary or None if operation not profiled
    """
    return _profile_stats.get(operation)


def log_profile_summary() -> None:
    """Log a summary of all profiling statistics."""
    if not _profile_stats:
        logger.info("no_profiling_data")
        return

    logger.info("profile_summary_start", total_operations=len(_profile_stats))

    # Sort by total time descending
    sorted_ops = sorted(
        _profile_stats.items(),
        key=lambda x: x[1]["total_seconds"],
        reverse=True,
    )

    for operation, stats in sorted_ops:
        logger.info(
            "operation_stats",
            operation=operation,
            count=stats["count"],
            total_seconds=round(stats["total_seconds"], 3),
            avg_seconds=round(stats["avg_seconds"], 3),
            min_seconds=round(stats["min_seconds"], 3),
            max_seconds=round(stats["max_seconds"], 3),
        )

    logger.info("profile_summary_end")
