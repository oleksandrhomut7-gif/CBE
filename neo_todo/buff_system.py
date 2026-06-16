"""Buff system module for micro-action rewards.

Implements the buff/micro-action system where small healthy habits
(drinking water, eye exercises, stretching) provide temporary percentage
bonuses to the daily efficiency index.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class Buff:
    """Represents a single active buff from a micro-action."""

    name: str
    bonus_percent: float
    duration_minutes: float
    activated_at: float = field(default_factory=time.time)
    id: str = field(default_factory=lambda: str(uuid4()))

    @property
    def bonus_multiplier(self) -> float:
        """Convert percentage bonus to multiplier (e.g., 5% -> 1.05)."""
        return 1.0 + (self.bonus_percent / 100.0)


@dataclass
class BuffTemplate:
    """Template defining a type of buff that can be activated."""

    name: str
    bonus_percent: float
    duration_minutes: float
    cooldown_minutes: float = 0.0


class BuffSystem:
    """Manages active buffs and their effect on efficiency.

    Buffs stack additively: two +5% buffs = +10% total bonus.
    Each buff has a duration and expires after that time.
    """

    DEFAULT_TEMPLATES: list[BuffTemplate] = [
        BuffTemplate(name="Water", bonus_percent=5.0, duration_minutes=30.0, cooldown_minutes=15.0),
        BuffTemplate(name="Eye Rest", bonus_percent=5.0, duration_minutes=20.0, cooldown_minutes=20.0),
        BuffTemplate(name="Stretch", bonus_percent=5.0, duration_minutes=25.0, cooldown_minutes=30.0),
    ]

    def __init__(self, time_func: object = None) -> None:
        """Initialize the buff system.

        Args:
            time_func: Optional callable returning current time in seconds.
                       Defaults to time.time. Useful for testing.
        """
        self._time_func = time_func if time_func is not None else time.time
        self._active_buffs: list[Buff] = []
        self._templates: list[BuffTemplate] = list(self.DEFAULT_TEMPLATES)
        self._activation_history: dict[str, float] = {}

    @property
    def active_buffs(self) -> list[Buff]:
        """List of currently active (non-expired) buffs."""
        self._cleanup_expired()
        return list(self._active_buffs)

    @property
    def total_bonus_percent(self) -> float:
        """Total additive bonus percentage from all active buffs."""
        self._cleanup_expired()
        return sum(b.bonus_percent for b in self._active_buffs)

    @property
    def total_multiplier(self) -> float:
        """Total multiplier to apply to efficiency index.

        Buffs stack additively: two +5% buffs = 1.10 multiplier.
        """
        return 1.0 + (self.total_bonus_percent / 100.0)

    @property
    def templates(self) -> list[BuffTemplate]:
        """Available buff templates."""
        return list(self._templates)

    def add_template(self, template: BuffTemplate) -> None:
        """Add a new buff template.

        Args:
            template: The buff template to add.
        """
        self._templates.append(template)

    def activate_buff(self, template_name: str) -> Buff:
        """Activate a buff by template name.

        Args:
            template_name: Name of the buff template to activate.

        Returns:
            The newly created active buff.

        Raises:
            ValueError: If template not found or buff is on cooldown.
        """
        template = self._find_template(template_name)
        self._check_cooldown(template)

        now = self._time_func()
        buff = Buff(
            name=template.name,
            bonus_percent=template.bonus_percent,
            duration_minutes=template.duration_minutes,
            activated_at=now,
        )
        self._active_buffs.append(buff)
        self._activation_history[template.name] = now
        return buff

    def is_on_cooldown(self, template_name: str) -> bool:
        """Check if a buff template is currently on cooldown.

        Args:
            template_name: Name of the buff template.

        Returns:
            True if the buff is on cooldown and cannot be activated.
        """
        template = self._find_template(template_name)
        if template.cooldown_minutes <= 0:
            return False

        last_activation = self._activation_history.get(template.name)
        if last_activation is None:
            return False

        now = self._time_func()
        elapsed_minutes = (now - last_activation) / 60.0
        return elapsed_minutes < template.cooldown_minutes

    def cooldown_remaining_minutes(self, template_name: str) -> float:
        """Get remaining cooldown time for a buff template.

        Args:
            template_name: Name of the buff template.

        Returns:
            Remaining cooldown in minutes, or 0.0 if not on cooldown.
        """
        template = self._find_template(template_name)
        if template.cooldown_minutes <= 0:
            return 0.0

        last_activation = self._activation_history.get(template.name)
        if last_activation is None:
            return 0.0

        now = self._time_func()
        elapsed_minutes = (now - last_activation) / 60.0
        remaining = template.cooldown_minutes - elapsed_minutes
        return max(0.0, remaining)

    def reset(self) -> None:
        """Reset all buffs for a new day."""
        self._active_buffs.clear()
        self._activation_history.clear()

    def _cleanup_expired(self) -> None:
        """Remove expired buffs from the active list."""
        now = self._time_func()
        self._active_buffs = [
            b for b in self._active_buffs
            if (now - b.activated_at) / 60.0 < b.duration_minutes
        ]

    def _find_template(self, name: str) -> BuffTemplate:
        """Find a buff template by name.

        Raises:
            ValueError: If no template with the given name exists.
        """
        for template in self._templates:
            if template.name == name:
                return template
        raise ValueError(f"No buff template named '{name}'")

    def _check_cooldown(self, template: BuffTemplate) -> None:
        """Check if a template is on cooldown.

        Raises:
            ValueError: If the buff is still on cooldown.
        """
        if self.is_on_cooldown(template.name):
            remaining = self.cooldown_remaining_minutes(template.name)
            raise ValueError(
                f"Buff '{template.name}' is on cooldown. "
                f"{remaining:.1f} minutes remaining."
            )
