"""Focus timer module for managing work/rest states.

Implements the "In Game" vs "On the Bench" paradigm:
- Focus (In Game): Timer running, index is dynamic.
- Pause (On the Bench): Timer stopped, index frozen.
"""

from __future__ import annotations

import time
from enum import Enum, auto


class TimerState(Enum):
    """Possible states of the focus timer."""

    IDLE = auto()
    FOCUSED = auto()
    PAUSED = auto()


class FocusTimer:
    """Manages focus and pause sessions.

    Tracks total focused time and supports starting, pausing, and resuming
    focus sessions. The timer does not accumulate time while paused.
    """

    def __init__(self, time_func: object = None) -> None:
        """Initialize the focus timer.

        Args:
            time_func: Optional callable returning current time in seconds.
                       Defaults to time.time. Useful for testing.
        """
        self._time_func = time_func if time_func is not None else time.time
        self._state: TimerState = TimerState.IDLE
        self._focus_start: float = 0.0
        self._total_focus_seconds: float = 0.0
        self._session_count: int = 0

    @property
    def state(self) -> TimerState:
        """Current state of the timer."""
        return self._state

    @property
    def is_focused(self) -> bool:
        """Whether the timer is currently in focus mode."""
        return self._state == TimerState.FOCUSED

    @property
    def is_paused(self) -> bool:
        """Whether the timer is currently paused."""
        return self._state == TimerState.PAUSED

    @property
    def is_idle(self) -> bool:
        """Whether the timer hasn't been started yet."""
        return self._state == TimerState.IDLE

    @property
    def session_count(self) -> int:
        """Number of focus sessions started today."""
        return self._session_count

    @property
    def total_focus_seconds(self) -> float:
        """Total accumulated focus time in seconds (not including current session)."""
        return self._total_focus_seconds

    @property
    def elapsed_focus_seconds(self) -> float:
        """Total focus time including current running session."""
        if self._state == TimerState.FOCUSED:
            current_time = self._time_func()
            return self._total_focus_seconds + (current_time - self._focus_start)
        return self._total_focus_seconds

    @property
    def elapsed_focus_minutes(self) -> float:
        """Total focus time in minutes including current running session."""
        return self.elapsed_focus_seconds / 60.0

    def start_focus(self) -> None:
        """Start or resume a focus session.

        Raises:
            ValueError: If already in focus mode.
        """
        if self._state == TimerState.FOCUSED:
            raise ValueError("Already in focus mode.")
        self._focus_start = self._time_func()
        self._state = TimerState.FOCUSED
        self._session_count += 1

    def pause(self) -> float:
        """Pause the current focus session.

        Returns:
            The duration of the just-ended focus segment in seconds.

        Raises:
            ValueError: If not currently in focus mode.
        """
        if self._state != TimerState.FOCUSED:
            raise ValueError("Cannot pause: not in focus mode.")

        current_time = self._time_func()
        segment_duration = current_time - self._focus_start
        self._total_focus_seconds += segment_duration
        self._state = TimerState.PAUSED
        return segment_duration

    def stop(self) -> float:
        """Stop the timer entirely and return total focus time.

        Returns:
            Total focus time accumulated in seconds.

        Raises:
            ValueError: If timer is idle.
        """
        if self._state == TimerState.IDLE:
            raise ValueError("Timer is not running.")

        if self._state == TimerState.FOCUSED:
            current_time = self._time_func()
            self._total_focus_seconds += current_time - self._focus_start

        total = self._total_focus_seconds
        self._state = TimerState.IDLE
        return total

    def reset(self) -> None:
        """Reset the timer for a new day."""
        self._state = TimerState.IDLE
        self._focus_start = 0.0
        self._total_focus_seconds = 0.0
        self._session_count = 0
