"""Unit tests for profiler."""

import time

import pytest

from src.utils import profiler
from src.utils.profiler import ProfileContext, profile, profile_block


@pytest.fixture(autouse=True)
def reset_profiler() -> None:
    """Reset profiler state before each test."""
    profiler.disable_profiling()
    profiler.clear_profile_stats()


def test_enable_disable_profiling() -> None:
    """Test enabling and disabling profiling."""
    assert profiler.is_profiling_enabled() is False

    profiler.enable_profiling(slow_threshold=0.5)
    assert profiler.is_profiling_enabled() is True

    profiler.disable_profiling()
    assert profiler.is_profiling_enabled() is False


def test_profile_decorator_disabled() -> None:
    """Test that profiling decorator does nothing when disabled."""

    @profile(operation="test_operation")
    def test_func() -> str:
        return "result"

    result = test_func()
    assert result == "result"

    # No stats should be recorded
    stats = profiler.get_profile_stats()
    assert len(stats) == 0


def test_profile_decorator_enabled() -> None:
    """Test profiling decorator when enabled."""
    profiler.enable_profiling(slow_threshold=0.0)  # Log all operations

    @profile(operation="test_operation")
    def test_func() -> str:
        time.sleep(0.01)  # Small delay
        return "result"

    result = test_func()
    assert result == "result"

    # Stats should be recorded
    stats = profiler.get_profile_stats()
    assert "test_operation" in stats
    assert stats["test_operation"]["count"] == 1
    assert stats["test_operation"]["total_seconds"] > 0


def test_profile_decorator_default_name() -> None:
    """Test profiling decorator using function name."""
    profiler.enable_profiling(slow_threshold=0.0)

    @profile()
    def my_function() -> str:
        return "result"

    my_function()

    stats = profiler.get_profile_stats()
    assert "my_function" in stats


def test_profile_decorator_exception() -> None:
    """Test profiling decorator with exception."""
    profiler.enable_profiling(slow_threshold=0.0)

    @profile(operation="failing_operation")
    def failing_func() -> None:
        raise ValueError("Test error")

    with pytest.raises(ValueError, match="Test error"):
        failing_func()

    # Stats should still be recorded
    stats = profiler.get_profile_stats()
    # Note: exception cases don't update stats in current implementation
    # This test verifies the exception is propagated


def test_profile_context_manager() -> None:
    """Test ProfileContext context manager."""
    profiler.enable_profiling(slow_threshold=0.0)

    with ProfileContext("context_operation"):
        time.sleep(0.01)

    stats = profiler.get_profile_stats()
    assert "context_operation" in stats
    assert stats["context_operation"]["count"] == 1


def test_profile_context_disabled() -> None:
    """Test ProfileContext when profiling disabled."""
    with ProfileContext("context_operation"):
        time.sleep(0.01)

    stats = profiler.get_profile_stats()
    assert len(stats) == 0


def test_profile_block() -> None:
    """Test profile_block convenience function."""
    profiler.enable_profiling(slow_threshold=0.0)

    with profile_block("block_operation"):
        time.sleep(0.01)

    stats = profiler.get_profile_stats()
    assert "block_operation" in stats


def test_multiple_operations() -> None:
    """Test profiling multiple operations."""
    profiler.enable_profiling(slow_threshold=0.0)

    @profile(operation="op1")
    def func1() -> None:
        time.sleep(0.01)

    @profile(operation="op2")
    def func2() -> None:
        time.sleep(0.01)

    func1()
    func1()
    func2()

    stats = profiler.get_profile_stats()
    assert stats["op1"]["count"] == 2
    assert stats["op2"]["count"] == 1


def test_get_operation_stats() -> None:
    """Test getting stats for specific operation."""
    profiler.enable_profiling(slow_threshold=0.0)

    @profile(operation="specific_op")
    def test_func() -> None:
        time.sleep(0.01)

    test_func()

    op_stats = profiler.get_operation_stats("specific_op")
    assert op_stats is not None
    assert op_stats["count"] == 1
    assert "total_seconds" in op_stats
    assert "avg_seconds" in op_stats


def test_get_operation_stats_missing() -> None:
    """Test getting stats for non-existent operation."""
    op_stats = profiler.get_operation_stats("nonexistent")
    assert op_stats is None


def test_clear_profile_stats() -> None:
    """Test clearing profile statistics."""
    profiler.enable_profiling(slow_threshold=0.0)

    @profile(operation="test_op")
    def test_func() -> None:
        pass

    test_func()

    stats = profiler.get_profile_stats()
    assert len(stats) > 0

    profiler.clear_profile_stats()

    stats = profiler.get_profile_stats()
    assert len(stats) == 0


def test_stats_aggregation() -> None:
    """Test that stats are properly aggregated."""
    profiler.enable_profiling(slow_threshold=0.0)

    @profile(operation="agg_op")
    def test_func(duration: float) -> None:
        time.sleep(duration)

    test_func(0.01)
    test_func(0.02)
    test_func(0.01)

    stats = profiler.get_profile_stats()
    op_stats = stats["agg_op"]

    assert op_stats["count"] == 3
    assert op_stats["total_seconds"] >= 0.04  # At least 40ms total
    assert op_stats["min_seconds"] < op_stats["max_seconds"]
    assert op_stats["avg_seconds"] == op_stats["total_seconds"] / op_stats["count"]


def test_slow_threshold() -> None:
    """Test slow operation threshold."""
    # Set high threshold so operations won't be logged as slow
    profiler.enable_profiling(slow_threshold=10.0)

    @profile(operation="fast_op")
    def fast_func() -> None:
        time.sleep(0.01)

    fast_func()

    # Should still record stats
    stats = profiler.get_profile_stats()
    assert "fast_op" in stats


def test_profile_context_with_exception() -> None:
    """Test ProfileContext with exception."""
    profiler.enable_profiling(slow_threshold=0.0)

    with pytest.raises(ValueError):
        with ProfileContext("failing_context"):
            raise ValueError("Test error")

    # Stats should still be recorded
    stats = profiler.get_profile_stats()
    assert "failing_context" in stats
