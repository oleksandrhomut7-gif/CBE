"""Tests for the FocusTimer module."""

import pytest

from neo_todo.focus_timer import FocusTimer, TimerState


class FakeClock:
    """Fake clock for deterministic timer testing."""

    def __init__(self, start: float = 0.0):
        self._now = start

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds


class TestFocusTimerStates:
    """Tests for timer state transitions."""

    def test_initial_state_is_idle(self):
        timer = FocusTimer(time_func=FakeClock())
        assert timer.state == TimerState.IDLE
        assert timer.is_idle
        assert not timer.is_focused
        assert not timer.is_paused

    def test_start_focus_transitions_to_focused(self):
        timer = FocusTimer(time_func=FakeClock())
        timer.start_focus()
        assert timer.state == TimerState.FOCUSED
        assert timer.is_focused

    def test_pause_transitions_to_paused(self):
        timer = FocusTimer(time_func=FakeClock())
        timer.start_focus()
        timer.pause()
        assert timer.state == TimerState.PAUSED
        assert timer.is_paused

    def test_resume_from_pause(self):
        timer = FocusTimer(time_func=FakeClock())
        timer.start_focus()
        timer.pause()
        timer.start_focus()
        assert timer.is_focused

    def test_stop_from_focused(self):
        clock = FakeClock()
        timer = FocusTimer(time_func=clock)
        timer.start_focus()
        clock.advance(60)
        total = timer.stop()
        assert timer.is_idle
        assert total == pytest.approx(60.0)

    def test_stop_from_paused(self):
        clock = FakeClock()
        timer = FocusTimer(time_func=clock)
        timer.start_focus()
        clock.advance(30)
        timer.pause()
        total = timer.stop()
        assert timer.is_idle
        assert total == pytest.approx(30.0)


class TestFocusTimerErrors:
    """Tests for invalid state transitions."""

    def test_start_when_already_focused_raises(self):
        timer = FocusTimer(time_func=FakeClock())
        timer.start_focus()
        with pytest.raises(ValueError, match="Already in focus mode"):
            timer.start_focus()

    def test_pause_when_not_focused_raises(self):
        timer = FocusTimer(time_func=FakeClock())
        with pytest.raises(ValueError, match="not in focus mode"):
            timer.pause()

    def test_pause_when_paused_raises(self):
        timer = FocusTimer(time_func=FakeClock())
        timer.start_focus()
        timer.pause()
        with pytest.raises(ValueError, match="not in focus mode"):
            timer.pause()

    def test_stop_when_idle_raises(self):
        timer = FocusTimer(time_func=FakeClock())
        with pytest.raises(ValueError, match="not running"):
            timer.stop()


class TestFocusTimerTimeTracking:
    """Tests for time accumulation logic."""

    def test_elapsed_during_focus(self):
        clock = FakeClock()
        timer = FocusTimer(time_func=clock)
        timer.start_focus()
        clock.advance(120)
        assert timer.elapsed_focus_seconds == pytest.approx(120.0)
        assert timer.elapsed_focus_minutes == pytest.approx(2.0)

    def test_elapsed_during_pause_is_frozen(self):
        clock = FakeClock()
        timer = FocusTimer(time_func=clock)
        timer.start_focus()
        clock.advance(60)
        timer.pause()
        clock.advance(999)  # time passes but not tracked
        assert timer.elapsed_focus_seconds == pytest.approx(60.0)

    def test_multiple_focus_sessions_accumulate(self):
        clock = FakeClock()
        timer = FocusTimer(time_func=clock)

        timer.start_focus()
        clock.advance(60)
        timer.pause()

        timer.start_focus()
        clock.advance(40)
        timer.pause()

        assert timer.elapsed_focus_seconds == pytest.approx(100.0)

    def test_pause_returns_segment_duration(self):
        clock = FakeClock()
        timer = FocusTimer(time_func=clock)
        timer.start_focus()
        clock.advance(45)
        duration = timer.pause()
        assert duration == pytest.approx(45.0)

    def test_total_focus_seconds_property(self):
        clock = FakeClock()
        timer = FocusTimer(time_func=clock)
        timer.start_focus()
        clock.advance(30)
        timer.pause()
        assert timer.total_focus_seconds == pytest.approx(30.0)


class TestFocusTimerSessionCount:
    """Tests for session counting."""

    def test_session_count_initial(self):
        timer = FocusTimer(time_func=FakeClock())
        assert timer.session_count == 0

    def test_session_count_increments(self):
        timer = FocusTimer(time_func=FakeClock())
        timer.start_focus()
        assert timer.session_count == 1
        timer.pause()
        timer.start_focus()
        assert timer.session_count == 2


class TestFocusTimerReset:
    """Tests for daily reset."""

    def test_reset_clears_everything(self):
        clock = FakeClock()
        timer = FocusTimer(time_func=clock)
        timer.start_focus()
        clock.advance(100)
        timer.pause()

        timer.reset()

        assert timer.is_idle
        assert timer.total_focus_seconds == 0.0
        assert timer.elapsed_focus_seconds == 0.0
        assert timer.session_count == 0
