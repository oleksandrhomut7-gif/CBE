"""Tests for the EfficiencyIndex module."""

import pytest

from neo_todo.efficiency_index import EfficiencyIndex


class TestEfficiencyIndexCalculation:
    """Tests for core index calculation logic."""

    def test_initial_value_is_zero(self):
        idx = EfficiencyIndex()
        assert idx.value == 0.0
        assert idx.raw_value == 0.0

    def test_zero_focus_time_returns_zero(self):
        idx = EfficiencyIndex()
        idx.add_completed_points(100)
        assert idx.value == 0.0

    def test_basic_calculation(self):
        idx = EfficiencyIndex()
        idx.add_completed_points(50)
        idx.add_focus_time(100)
        assert idx.raw_value == pytest.approx(0.5)

    def test_multiple_task_completions(self):
        idx = EfficiencyIndex()
        idx.add_completed_points(10)
        idx.add_completed_points(30)
        idx.add_completed_points(60)
        idx.add_focus_time(100)
        assert idx.raw_value == pytest.approx(1.0)

    def test_increasing_focus_time_decreases_index(self):
        idx = EfficiencyIndex()
        idx.add_completed_points(50)
        idx.add_focus_time(50)
        value_at_50 = idx.raw_value

        idx.add_focus_time(50)
        value_at_100 = idx.raw_value

        assert value_at_100 < value_at_50

    def test_properties_track_state(self):
        idx = EfficiencyIndex()
        idx.add_completed_points(42)
        idx.add_focus_time(10)
        assert idx.completed_points == 42.0
        assert idx.focus_time_minutes == 10.0


class TestEfficiencyIndexBuffs:
    """Tests for buff multiplier application."""

    def test_default_multiplier_is_one(self):
        idx = EfficiencyIndex()
        assert idx.buff_multiplier == 1.0

    def test_buff_multiplier_applied(self):
        idx = EfficiencyIndex()
        idx.add_completed_points(50)
        idx.add_focus_time(100)
        idx.set_buff_multiplier(1.10)
        assert idx.value == pytest.approx(0.55)

    def test_raw_value_unaffected_by_buff(self):
        idx = EfficiencyIndex()
        idx.add_completed_points(50)
        idx.add_focus_time(100)
        idx.set_buff_multiplier(1.10)
        assert idx.raw_value == pytest.approx(0.5)

    def test_buff_multiplier_below_one_raises(self):
        idx = EfficiencyIndex()
        with pytest.raises(ValueError, match="cannot be less than 1.0"):
            idx.set_buff_multiplier(0.9)


class TestEfficiencyIndexFormatting:
    """Tests for sports-style index formatting."""

    def test_format_zero(self):
        idx = EfficiencyIndex()
        assert idx.format_index() == ".000"

    def test_format_typical_value(self):
        idx = EfficiencyIndex()
        idx.add_completed_points(413)
        idx.add_focus_time(1000)
        assert idx.format_index() == ".413"

    def test_format_high_value(self):
        idx = EfficiencyIndex()
        idx.add_completed_points(650)
        idx.add_focus_time(1000)
        assert idx.format_index() == ".650"

    def test_format_rounds_correctly(self):
        idx = EfficiencyIndex()
        idx.add_completed_points(1)
        idx.add_focus_time(3)
        formatted = idx.format_index()
        assert len(formatted) == 4  # dot + 3 digits
        assert formatted.startswith(".")


class TestEfficiencyIndexValidation:
    """Tests for input validation."""

    def test_negative_points_raises(self):
        idx = EfficiencyIndex()
        with pytest.raises(ValueError, match="cannot be negative"):
            idx.add_completed_points(-10)

    def test_negative_focus_time_raises(self):
        idx = EfficiencyIndex()
        with pytest.raises(ValueError, match="cannot be negative"):
            idx.add_focus_time(-5)

    def test_zero_points_allowed(self):
        idx = EfficiencyIndex()
        idx.add_completed_points(0)
        assert idx.completed_points == 0.0

    def test_zero_focus_time_allowed(self):
        idx = EfficiencyIndex()
        idx.add_focus_time(0)
        assert idx.focus_time_minutes == 0.0


class TestEfficiencyIndexReset:
    """Tests for daily reset functionality."""

    def test_reset_clears_all(self):
        idx = EfficiencyIndex()
        idx.add_completed_points(100)
        idx.add_focus_time(60)
        idx.set_buff_multiplier(1.1)

        idx.reset()

        assert idx.completed_points == 0.0
        assert idx.focus_time_minutes == 0.0
        assert idx.buff_multiplier == 1.0
        assert idx.value == 0.0
