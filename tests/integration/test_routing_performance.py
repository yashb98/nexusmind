"""Test parallel I/O routing — verify asyncio.gather is faster than sequential."""

import asyncio
import time


async def _slow_operation(delay: float = 0.1) -> str:
    """Simulate a 100ms database call."""
    await asyncio.sleep(delay)
    return "done"


class TestParallelRouting:
    async def test_parallel_faster_than_sequential(self) -> None:
        """Three 100ms operations should take ~100ms in parallel, not ~300ms."""
        # Sequential
        start = time.monotonic()
        await _slow_operation()
        await _slow_operation()
        await _slow_operation()
        sequential_time = time.monotonic() - start

        # Parallel
        start = time.monotonic()
        await asyncio.gather(
            _slow_operation(),
            _slow_operation(),
            _slow_operation(),
        )
        parallel_time = time.monotonic() - start

        # Parallel should be significantly faster
        assert parallel_time < sequential_time * 0.6
        # Parallel should be under 150ms for 100ms operations
        assert parallel_time < 0.15

    async def test_gather_returns_all_results(self) -> None:
        """asyncio.gather should return results in order."""
        results = await asyncio.gather(
            _slow_operation(0.01),
            _slow_operation(0.01),
            _slow_operation(0.01),
        )
        assert len(results) == 3
        assert all(r == "done" for r in results)
