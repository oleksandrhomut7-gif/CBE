"""Integration tests combining multiple modules in realistic workflows."""

import pytest

from neo_todo.buff_system import BuffSystem
from neo_todo.efficiency_index import EfficiencyIndex
from neo_todo.focus_timer import FocusTimer
from neo_todo.task_manager import Task, TaskDifficulty, TaskManager


class FakeClock:
    """Fake clock for deterministic integration testing."""

    def __init__(self, start: float = 0.0):
        self._now = start

    def __call__(self) -> float:
        return self._now

    def advance(self, seconds: float) -> None:
        self._now += seconds

    def advance_minutes(self, minutes: float) -> None:
        self._now += minutes * 60.0


class TestFullDayWorkflow:
    """Simulate a full day of using Neo-ToDo."""

    def test_morning_plan_focus_complete_cycle(self):
        clock = FakeClock()
        mgr = TaskManager(backpack_capacity=300)
        timer = FocusTimer(time_func=clock)
        index = EfficiencyIndex()

        # Morning: Plan tasks
        t1 = Task(title="Review PRs", difficulty=TaskDifficulty.MEDIUM)
        t2 = Task(title="Write feature", difficulty=TaskDifficulty.HARD)
        t3 = Task(title="Update docs", difficulty=TaskDifficulty.EASY)
        mgr.add_to_backpack(t1)
        mgr.add_to_backpack(t2)
        mgr.add_to_backpack(t3)
        assert mgr.backpack_points_used == 100

        # Start first focus session
        mgr.move_to_court(t1.id)
        timer.start_focus()
        clock.advance_minutes(25)

        # Complete task
        timer.pause()
        completed = mgr.complete_court_task()
        index.add_completed_points(completed.points)
        index.add_focus_time(timer.elapsed_focus_minutes)

        assert index.raw_value == pytest.approx(30 / 25)

    def test_buff_affects_efficiency(self):
        clock = FakeClock()
        mgr = TaskManager()
        timer = FocusTimer(time_func=clock)
        index = EfficiencyIndex()
        buffs = BuffSystem(time_func=clock)

        # Add and complete a task
        task = Task(title="Quick fix", difficulty=TaskDifficulty.EASY)
        mgr.add_to_backpack(task)
        mgr.move_to_court(task.id)
        timer.start_focus()
        clock.advance_minutes(10)
        timer.pause()
        mgr.complete_court_task()

        index.add_completed_points(task.points)
        index.add_focus_time(timer.elapsed_focus_minutes)

        raw_before_buff = index.raw_value

        # Activate a buff
        buffs.activate_buff("Water")
        index.set_buff_multiplier(buffs.total_multiplier)

        assert index.value > raw_before_buff
        assert index.value == pytest.approx(raw_before_buff * 1.05)

    def test_returning_task_and_switching(self):
        mgr = TaskManager()
        t1 = Task(title="Hard task", difficulty=TaskDifficulty.EPIC)
        t2 = Task(title="Easy win", difficulty=TaskDifficulty.EASY)
        mgr.add_to_backpack(t1)
        mgr.add_to_backpack(t2)

        # Start hard task, decide to switch
        mgr.move_to_court(t1.id)
        mgr.return_to_backpack()

        # Do easy task instead
        mgr.move_to_court(t2.id)
        mgr.complete_court_task()

        assert mgr.total_completed_points == 10
        assert len(mgr.backpack) == 1
        assert mgr.backpack[0].id == t1.id

    def test_efficiency_decreases_over_idle_focus_time(self):
        clock = FakeClock()
        timer = FocusTimer(time_func=clock)
        index = EfficiencyIndex()

        # Complete one task worth 30 points after 10 minutes
        timer.start_focus()
        clock.advance_minutes(10)
        timer.pause()
        index.add_completed_points(30)
        index.add_focus_time(timer.elapsed_focus_minutes)
        value_after_first = index.value  # 30/10 = 3.0

        # Continue focusing but don't complete anything
        timer.start_focus()
        clock.advance_minutes(20)
        timer.pause()
        index.add_focus_time(20)  # Now 30 minutes total
        value_after_idle = index.value  # 30/30 = 1.0

        assert value_after_idle < value_after_first

    def test_pause_protects_index(self):
        clock = FakeClock()
        timer = FocusTimer(time_func=clock)
        index = EfficiencyIndex()

        # Work for 10 minutes and complete something
        timer.start_focus()
        clock.advance_minutes(10)
        timer.pause()
        index.add_completed_points(50)
        index.add_focus_time(timer.elapsed_focus_minutes)

        value_at_pause = index.value

        # Time passes while paused - index doesn't change
        clock.advance_minutes(60)
        assert index.value == value_at_pause
