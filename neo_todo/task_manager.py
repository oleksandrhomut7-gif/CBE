"""Task management module implementing the 3-Column Lifecycle.

Zones:
- Backpack (Plan): Tasks planned for the day with a capacity limit.
- Court (Focus): Single-task zone where active work happens.
- Completed (Trophies): Finished tasks that contribute to the efficiency index.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional
from uuid import uuid4


class TaskDifficulty(IntEnum):
    """Task difficulty levels with associated point values."""

    EASY = 10
    MEDIUM = 30
    HARD = 60
    EPIC = 100


@dataclass
class Task:
    """Represents a single task in the system."""

    title: str
    difficulty: TaskDifficulty
    id: str = field(default_factory=lambda: str(uuid4()))
    elapsed_minutes: float = 0.0

    @property
    def points(self) -> int:
        """Point value derived from difficulty."""
        return int(self.difficulty)


class TaskManager:
    """Manages the 3-column task lifecycle.

    Enforces:
    - Backpack capacity limit (max total points per day).
    - Single-task rule on the court.
    - Ordered flow: Backpack -> Court -> Completed (or Backpack <- Court).
    """

    DEFAULT_BACKPACK_CAPACITY = 300

    def __init__(self, backpack_capacity: int = DEFAULT_BACKPACK_CAPACITY) -> None:
        self._backpack_capacity = backpack_capacity
        self._backpack: list[Task] = []
        self._court: Optional[Task] = None
        self._completed: list[Task] = []

    @property
    def backpack_capacity(self) -> int:
        """Maximum total points allowed in the backpack."""
        return self._backpack_capacity

    @property
    def backpack(self) -> list[Task]:
        """Tasks in the backpack (plan) zone."""
        return list(self._backpack)

    @property
    def court_task(self) -> Optional[Task]:
        """The single task currently on the court (focus zone)."""
        return self._court

    @property
    def completed(self) -> list[Task]:
        """Tasks in the completed (trophies) zone."""
        return list(self._completed)

    @property
    def backpack_points_used(self) -> int:
        """Total points currently allocated in the backpack."""
        return sum(t.points for t in self._backpack)

    @property
    def backpack_points_remaining(self) -> int:
        """Points still available in the backpack."""
        return self._backpack_capacity - self.backpack_points_used

    @property
    def total_completed_points(self) -> int:
        """Sum of points from all completed tasks."""
        return sum(t.points for t in self._completed)

    def add_to_backpack(self, task: Task) -> None:
        """Add a task to the backpack zone.

        Args:
            task: The task to add.

        Raises:
            ValueError: If adding the task would exceed backpack capacity.
        """
        if self.backpack_points_used + task.points > self._backpack_capacity:
            raise ValueError(
                f"Cannot add task ({task.points} pts): "
                f"would exceed backpack capacity of {self._backpack_capacity} pts "
                f"(currently {self.backpack_points_used} pts used)"
            )
        self._backpack.append(task)

    def move_to_court(self, task_id: str) -> Task:
        """Move a task from the backpack to the court (focus zone).

        Args:
            task_id: ID of the task to move.

        Returns:
            The task that was moved to the court.

        Raises:
            ValueError: If court is already occupied or task not found.
        """
        if self._court is not None:
            raise ValueError(
                "Court is occupied. Complete or return the current task first."
            )

        task = self._find_and_remove_from_backpack(task_id)
        self._court = task
        return task

    def complete_court_task(self) -> Task:
        """Move the current court task to completed zone.

        Returns:
            The completed task.

        Raises:
            ValueError: If no task is on the court.
        """
        if self._court is None:
            raise ValueError("No task on the court to complete.")

        task = self._court
        self._court = None
        self._completed.append(task)
        return task

    def return_to_backpack(self) -> Task:
        """Return the court task back to the backpack.

        Returns:
            The task that was returned.

        Raises:
            ValueError: If no task is on the court.
        """
        if self._court is None:
            raise ValueError("No task on the court to return.")

        task = self._court
        self._court = None
        self._backpack.append(task)
        return task

    def remove_from_backpack(self, task_id: str) -> Task:
        """Remove a task from the backpack entirely.

        Args:
            task_id: ID of the task to remove.

        Returns:
            The removed task.

        Raises:
            ValueError: If task not found in backpack.
        """
        return self._find_and_remove_from_backpack(task_id)

    def _find_and_remove_from_backpack(self, task_id: str) -> Task:
        """Find and remove a task from the backpack by ID.

        Raises:
            ValueError: If task not found.
        """
        for i, task in enumerate(self._backpack):
            if task.id == task_id:
                return self._backpack.pop(i)
        raise ValueError(f"Task with id '{task_id}' not found in backpack.")
