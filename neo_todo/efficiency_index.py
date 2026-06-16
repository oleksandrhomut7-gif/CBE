"""Efficiency Index calculation module.

Implements the CBE (Career Best Effort) formula:
    Efficiency Index = Sum of points for completed tasks / Total active focus time (minutes)

The index is displayed in sports-style format: three decimal places without a leading zero
(e.g., ".413", ".650").
"""

from __future__ import annotations


class EfficiencyIndex:
    """Tracks and calculates the user's daily efficiency index."""

    def __init__(self) -> None:
        self._completed_points: float = 0.0
        self._focus_time_minutes: float = 0.0
        self._buff_multiplier: float = 1.0

    @property
    def completed_points(self) -> float:
        """Total points earned from completed tasks."""
        return self._completed_points

    @property
    def focus_time_minutes(self) -> float:
        """Total active focus time in minutes."""
        return self._focus_time_minutes

    @property
    def buff_multiplier(self) -> float:
        """Current buff multiplier applied to the index."""
        return self._buff_multiplier

    @property
    def raw_value(self) -> float:
        """Calculate the raw efficiency index value (without buffs)."""
        if self._focus_time_minutes <= 0:
            return 0.0
        return self._completed_points / self._focus_time_minutes

    @property
    def value(self) -> float:
        """Calculate the efficiency index with buff multiplier applied."""
        return self.raw_value * self._buff_multiplier

    def format_index(self) -> str:
        """Format the index in sports-style: '.XXX' (three decimal places, no leading zero).

        Returns:
            Formatted string like '.413' or '.000' if no activity.
        """
        val = self.value
        # Always show just the decimal portion with 3 digits
        decimal_part = val - int(val)
        return f"{decimal_part:.3f}"[1:]  # strip leading '0', keep '.'

    def add_completed_points(self, points: float) -> None:
        """Add points from a completed task.

        Args:
            points: The point value of the completed task.

        Raises:
            ValueError: If points is negative.
        """
        if points < 0:
            raise ValueError("Points cannot be negative")
        self._completed_points += points

    def add_focus_time(self, minutes: float) -> None:
        """Add elapsed focus time.

        Args:
            minutes: Minutes of active focus time to add.

        Raises:
            ValueError: If minutes is negative.
        """
        if minutes < 0:
            raise ValueError("Focus time cannot be negative")
        self._focus_time_minutes += minutes

    def set_buff_multiplier(self, multiplier: float) -> None:
        """Set the buff multiplier for the efficiency index.

        Args:
            multiplier: The multiplier value (must be >= 1.0).

        Raises:
            ValueError: If multiplier is less than 1.0.
        """
        if multiplier < 1.0:
            raise ValueError("Buff multiplier cannot be less than 1.0")
        self._buff_multiplier = multiplier

    def reset(self) -> None:
        """Reset the efficiency index for a new day."""
        self._completed_points = 0.0
        self._focus_time_minutes = 0.0
        self._buff_multiplier = 1.0
