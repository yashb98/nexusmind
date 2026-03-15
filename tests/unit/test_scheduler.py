"""Tests for background scheduler — mode selection, rate limiting, pause/resume."""

from src.services.scheduler import AgentScheduler


class TestSchedulerModeSelection:
    def test_picks_valid_mode(self) -> None:
        sched = AgentScheduler()
        for _ in range(20):
            mode = sched._pick_mode()
            assert mode in ("explore", "research", "refine")


class TestSchedulerState:
    def test_initial_state(self) -> None:
        sched = AgentScheduler()
        assert sched.running is False
        assert sched.paused is False
        assert sched.cycle_count == 0

    def test_pause_resume(self) -> None:
        sched = AgentScheduler()
        sched.pause()
        assert sched.paused is True
        sched.resume()
        assert sched.paused is False

    def test_stop(self) -> None:
        sched = AgentScheduler()
        sched.running = True
        sched.stop()
        assert sched.running is False

    def test_get_status(self) -> None:
        sched = AgentScheduler()
        status = sched.get_status()
        assert "running" in status
        assert "paused" in status
        assert "cycle_count" in status
        assert "mode_distribution" in status
        assert status["mode_distribution"]["explore"] == 0
