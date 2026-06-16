"""Tests for the TaskManager module."""

import pytest

from neo_todo.task_manager import Task, TaskDifficulty, TaskManager


class TestTask:
    """Tests for the Task dataclass."""

    def test_task_creation(self):
        task = Task(title="Write tests", difficulty=TaskDifficulty.MEDIUM)
        assert task.title == "Write tests"
        assert task.difficulty == TaskDifficulty.MEDIUM
        assert task.points == 30
        assert task.id is not None

    def test_task_points_match_difficulty(self):
        assert Task(title="a", difficulty=TaskDifficulty.EASY).points == 10
        assert Task(title="b", difficulty=TaskDifficulty.MEDIUM).points == 30
        assert Task(title="c", difficulty=TaskDifficulty.HARD).points == 60
        assert Task(title="d", difficulty=TaskDifficulty.EPIC).points == 100

    def test_tasks_have_unique_ids(self):
        t1 = Task(title="a", difficulty=TaskDifficulty.EASY)
        t2 = Task(title="b", difficulty=TaskDifficulty.EASY)
        assert t1.id != t2.id

    def test_task_elapsed_minutes_default(self):
        task = Task(title="x", difficulty=TaskDifficulty.EASY)
        assert task.elapsed_minutes == 0.0


class TestTaskManagerBackpack:
    """Tests for backpack zone operations."""

    def test_add_task_to_backpack(self):
        mgr = TaskManager()
        task = Task(title="Read docs", difficulty=TaskDifficulty.EASY)
        mgr.add_to_backpack(task)
        assert len(mgr.backpack) == 1
        assert mgr.backpack[0].id == task.id

    def test_backpack_capacity_tracking(self):
        mgr = TaskManager(backpack_capacity=100)
        mgr.add_to_backpack(Task(title="a", difficulty=TaskDifficulty.EASY))
        assert mgr.backpack_points_used == 10
        assert mgr.backpack_points_remaining == 90

    def test_exceed_backpack_capacity_raises(self):
        mgr = TaskManager(backpack_capacity=50)
        mgr.add_to_backpack(Task(title="a", difficulty=TaskDifficulty.MEDIUM))  # 30
        with pytest.raises(ValueError, match="exceed backpack capacity"):
            mgr.add_to_backpack(Task(title="b", difficulty=TaskDifficulty.MEDIUM))  # 30 > 20 remaining

    def test_exactly_at_capacity_allowed(self):
        mgr = TaskManager(backpack_capacity=100)
        mgr.add_to_backpack(Task(title="a", difficulty=TaskDifficulty.EPIC))  # 100
        assert mgr.backpack_points_used == 100
        assert mgr.backpack_points_remaining == 0

    def test_remove_from_backpack(self):
        mgr = TaskManager()
        task = Task(title="x", difficulty=TaskDifficulty.EASY)
        mgr.add_to_backpack(task)
        removed = mgr.remove_from_backpack(task.id)
        assert removed.id == task.id
        assert len(mgr.backpack) == 0

    def test_remove_nonexistent_raises(self):
        mgr = TaskManager()
        with pytest.raises(ValueError, match="not found in backpack"):
            mgr.remove_from_backpack("nonexistent-id")

    def test_multiple_tasks_in_backpack(self):
        mgr = TaskManager()
        tasks = [
            Task(title=f"task-{i}", difficulty=TaskDifficulty.EASY)
            for i in range(5)
        ]
        for t in tasks:
            mgr.add_to_backpack(t)
        assert len(mgr.backpack) == 5
        assert mgr.backpack_points_used == 50


class TestTaskManagerCourt:
    """Tests for court (focus) zone operations."""

    def test_move_to_court(self):
        mgr = TaskManager()
        task = Task(title="Focus task", difficulty=TaskDifficulty.HARD)
        mgr.add_to_backpack(task)
        moved = mgr.move_to_court(task.id)
        assert moved.id == task.id
        assert mgr.court_task is not None
        assert mgr.court_task.id == task.id
        assert len(mgr.backpack) == 0

    def test_court_single_task_rule(self):
        mgr = TaskManager()
        t1 = Task(title="first", difficulty=TaskDifficulty.EASY)
        t2 = Task(title="second", difficulty=TaskDifficulty.EASY)
        mgr.add_to_backpack(t1)
        mgr.add_to_backpack(t2)
        mgr.move_to_court(t1.id)

        with pytest.raises(ValueError, match="Court is occupied"):
            mgr.move_to_court(t2.id)

    def test_move_nonexistent_to_court_raises(self):
        mgr = TaskManager()
        with pytest.raises(ValueError, match="not found in backpack"):
            mgr.move_to_court("bad-id")

    def test_court_initially_empty(self):
        mgr = TaskManager()
        assert mgr.court_task is None


class TestTaskManagerCompleted:
    """Tests for completing tasks."""

    def test_complete_court_task(self):
        mgr = TaskManager()
        task = Task(title="Complete me", difficulty=TaskDifficulty.MEDIUM)
        mgr.add_to_backpack(task)
        mgr.move_to_court(task.id)
        completed = mgr.complete_court_task()

        assert completed.id == task.id
        assert mgr.court_task is None
        assert len(mgr.completed) == 1
        assert mgr.total_completed_points == 30

    def test_complete_empty_court_raises(self):
        mgr = TaskManager()
        with pytest.raises(ValueError, match="No task on the court"):
            mgr.complete_court_task()

    def test_multiple_completions_accumulate_points(self):
        mgr = TaskManager()
        for i in range(3):
            t = Task(title=f"t-{i}", difficulty=TaskDifficulty.EASY)
            mgr.add_to_backpack(t)
            mgr.move_to_court(t.id)
            mgr.complete_court_task()

        assert mgr.total_completed_points == 30
        assert len(mgr.completed) == 3


class TestTaskManagerReturnToBackpack:
    """Tests for returning tasks from court to backpack."""

    def test_return_to_backpack(self):
        mgr = TaskManager()
        task = Task(title="Return me", difficulty=TaskDifficulty.HARD)
        mgr.add_to_backpack(task)
        mgr.move_to_court(task.id)
        returned = mgr.return_to_backpack()

        assert returned.id == task.id
        assert mgr.court_task is None
        assert len(mgr.backpack) == 1

    def test_return_empty_court_raises(self):
        mgr = TaskManager()
        with pytest.raises(ValueError, match="No task on the court"):
            mgr.return_to_backpack()


class TestTaskManagerFullWorkflow:
    """Integration tests for the full task lifecycle."""

    def test_full_lifecycle(self):
        mgr = TaskManager(backpack_capacity=300)

        t1 = Task(title="Plan architecture", difficulty=TaskDifficulty.HARD)
        t2 = Task(title="Write README", difficulty=TaskDifficulty.EASY)
        t3 = Task(title="Deploy", difficulty=TaskDifficulty.EPIC)

        mgr.add_to_backpack(t1)
        mgr.add_to_backpack(t2)
        mgr.add_to_backpack(t3)
        assert mgr.backpack_points_used == 170

        mgr.move_to_court(t1.id)
        assert len(mgr.backpack) == 2

        mgr.complete_court_task()
        assert mgr.total_completed_points == 60

        mgr.move_to_court(t3.id)
        mgr.return_to_backpack()
        assert mgr.court_task is None
        assert len(mgr.backpack) == 2

        mgr.move_to_court(t2.id)
        mgr.complete_court_task()
        assert mgr.total_completed_points == 70
