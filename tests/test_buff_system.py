"""Tests for the BuffSystem module."""

import pytest

from neo_todo.buff_system import Buff, BuffSystem, BuffTemplate


class FakeClock:
    """Fake clock for deterministic buff testing."""

    def __init__(self, start: float = 0.0):
        self._now = start

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds

    def advance_minutes(self, minutes: float) -> None:
        self._now += minutes * 60.0


class TestBuff:
    """Tests for the Buff dataclass."""

    def test_buff_creation(self):
        buff = Buff(name="Water", bonus_percent=5.0, duration_minutes=30.0)
        assert buff.name == "Water"
        assert buff.bonus_percent == 5.0
        assert buff.duration_minutes == 30.0
        assert buff.id is not None

    def test_bonus_multiplier(self):
        buff = Buff(name="Stretch", bonus_percent=5.0, duration_minutes=20.0)
        assert buff.bonus_multiplier == pytest.approx(1.05)

    def test_bonus_multiplier_ten_percent(self):
        buff = Buff(name="Big buff", bonus_percent=10.0, duration_minutes=10.0)
        assert buff.bonus_multiplier == pytest.approx(1.10)


class TestBuffSystemActivation:
    """Tests for activating buffs."""

    def test_activate_buff(self):
        clock = FakeClock()
        system = BuffSystem(time_func=clock)
        buff = system.activate_buff("Water")
        assert buff.name == "Water"
        assert buff.bonus_percent == 5.0
        assert len(system.active_buffs) == 1

    def test_activate_nonexistent_template_raises(self):
        system = BuffSystem(time_func=FakeClock())
        with pytest.raises(ValueError, match="No buff template"):
            system.activate_buff("Nonexistent")

    def test_activate_multiple_buffs(self):
        clock = FakeClock()
        system = BuffSystem(time_func=clock)
        system.activate_buff("Water")
        clock.advance_minutes(20)  # past Water cooldown
        system.activate_buff("Stretch")
        assert len(system.active_buffs) == 2


class TestBuffSystemBonusCalculation:
    """Tests for bonus percentage and multiplier calculation."""

    def test_no_active_buffs_no_bonus(self):
        system = BuffSystem(time_func=FakeClock())
        assert system.total_bonus_percent == 0.0
        assert system.total_multiplier == pytest.approx(1.0)

    def test_single_buff_bonus(self):
        system = BuffSystem(time_func=FakeClock())
        system.activate_buff("Water")
        assert system.total_bonus_percent == pytest.approx(5.0)
        assert system.total_multiplier == pytest.approx(1.05)

    def test_multiple_buffs_stack_additively(self):
        clock = FakeClock()
        system = BuffSystem(time_func=clock)
        system.activate_buff("Water")
        clock.advance_minutes(20)
        system.activate_buff("Stretch")
        assert system.total_bonus_percent == pytest.approx(10.0)
        assert system.total_multiplier == pytest.approx(1.10)


class TestBuffSystemExpiration:
    """Tests for buff expiration logic."""

    def test_buff_expires_after_duration(self):
        clock = FakeClock()
        system = BuffSystem(time_func=clock)
        system.activate_buff("Water")  # 30 min duration
        clock.advance_minutes(31)
        assert len(system.active_buffs) == 0
        assert system.total_bonus_percent == 0.0

    def test_buff_active_before_expiration(self):
        clock = FakeClock()
        system = BuffSystem(time_func=clock)
        system.activate_buff("Water")  # 30 min duration
        clock.advance_minutes(29)
        assert len(system.active_buffs) == 1

    def test_partial_expiration(self):
        clock = FakeClock()
        system = BuffSystem(time_func=clock)
        system.activate_buff("Eye Rest")  # 20 min duration
        clock.advance_minutes(21)
        system.activate_buff("Stretch")  # 25 min duration, activated fresh
        assert len(system.active_buffs) == 1
        assert system.active_buffs[0].name == "Stretch"


class TestBuffSystemCooldown:
    """Tests for cooldown mechanics."""

    def test_cooldown_prevents_reactivation(self):
        clock = FakeClock()
        system = BuffSystem(time_func=clock)
        system.activate_buff("Water")  # cooldown: 15 min
        clock.advance_minutes(5)
        with pytest.raises(ValueError, match="on cooldown"):
            system.activate_buff("Water")

    def test_cooldown_expires(self):
        clock = FakeClock()
        system = BuffSystem(time_func=clock)
        system.activate_buff("Water")  # cooldown: 15 min
        clock.advance_minutes(16)
        buff = system.activate_buff("Water")
        assert buff.name == "Water"

    def test_is_on_cooldown(self):
        clock = FakeClock()
        system = BuffSystem(time_func=clock)
        system.activate_buff("Water")
        assert system.is_on_cooldown("Water") is True
        clock.advance_minutes(16)
        assert system.is_on_cooldown("Water") is False

    def test_cooldown_remaining_minutes(self):
        clock = FakeClock()
        system = BuffSystem(time_func=clock)
        system.activate_buff("Water")  # cooldown: 15 min
        clock.advance_minutes(10)
        remaining = system.cooldown_remaining_minutes("Water")
        assert remaining == pytest.approx(5.0)

    def test_cooldown_remaining_when_not_activated(self):
        system = BuffSystem(time_func=FakeClock())
        assert system.cooldown_remaining_minutes("Water") == 0.0

    def test_is_on_cooldown_nonexistent_raises(self):
        system = BuffSystem(time_func=FakeClock())
        with pytest.raises(ValueError, match="No buff template"):
            system.is_on_cooldown("Nonexistent")


class TestBuffSystemTemplates:
    """Tests for buff template management."""

    def test_default_templates_exist(self):
        system = BuffSystem(time_func=FakeClock())
        names = [t.name for t in system.templates]
        assert "Water" in names
        assert "Eye Rest" in names
        assert "Stretch" in names

    def test_add_custom_template(self):
        system = BuffSystem(time_func=FakeClock())
        custom = BuffTemplate(
            name="Meditation", bonus_percent=8.0, duration_minutes=45.0
        )
        system.add_template(custom)
        buff = system.activate_buff("Meditation")
        assert buff.bonus_percent == 8.0

    def test_template_without_cooldown(self):
        clock = FakeClock()
        system = BuffSystem(time_func=clock)
        system.add_template(
            BuffTemplate(name="NoCooldown", bonus_percent=3.0, duration_minutes=10.0, cooldown_minutes=0.0)
        )
        system.activate_buff("NoCooldown")
        system.activate_buff("NoCooldown")  # should not raise
        assert len(system.active_buffs) == 2


class TestBuffSystemReset:
    """Tests for daily reset."""

    def test_reset_clears_buffs(self):
        clock = FakeClock()
        system = BuffSystem(time_func=clock)
        system.activate_buff("Water")
        system.reset()
        assert len(system.active_buffs) == 0
        assert system.total_bonus_percent == 0.0

    def test_reset_clears_cooldowns(self):
        clock = FakeClock()
        system = BuffSystem(time_func=clock)
        system.activate_buff("Water")
        system.reset()
        assert system.is_on_cooldown("Water") is False
