"""PawPal+ core system.

Class skeleton generated from diagrams/uml.mmd (priority + time-budget design).
Attributes and method signatures only — scheduling logic comes next.
"""

from __future__ import annotations

from enum import Enum


class Priority(Enum):
    """How important a task is. Drives ranking in the scheduler."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Owner:
    """The pet owner and their constraints."""

    def __init__(self, name: str, available_minutes: int, preferences: list[str] | None = None):
        self.name = name
        self.available_minutes = available_minutes
        self.preferences = preferences if preferences is not None else []


class Pet:
    """The pet the plan is for."""

    def __init__(self, name: str, species: str, breed: str = ""):
        self.name = name
        self.species = species
        self.breed = breed


class Task:
    """One care activity: what it is, how long it takes, how important."""

    def __init__(self, title: str, duration_minutes: int, priority: Priority, category: str = ""):
        self.title = title
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.category = category

    def rank(self) -> int:
        """Return a sortable integer for this task's priority (higher = more important)."""
        raise NotImplementedError


class PlanItem:
    """A scheduler decision about a single task: included/skipped, when, and why."""

    def __init__(self, task: Task, start_time: str, included: bool, reason: str):
        self.task = task
        self.start_time = start_time
        self.included = included
        self.reason = reason


class DailyPlan:
    """The result of scheduling: what got in, what got skipped, and the explanation."""

    def __init__(
        self,
        pet: Pet,
        owner: Owner,
        items: list[PlanItem] | None = None,
        skipped: list[PlanItem] | None = None,
        total_minutes: int = 0,
    ):
        self.pet = pet
        self.owner = owner
        self.items = items if items is not None else []
        self.skipped = skipped if skipped is not None else []
        self.total_minutes = total_minutes

    def explain(self) -> str:
        """Return a human-readable explanation of the plan and its choices."""
        raise NotImplementedError


class Scheduler:
    """Ranks tasks by priority, fits them into the owner's time budget, builds a DailyPlan."""

    def __init__(self, start_hour: int = 8):
        self.start_hour = start_hour

    def build_plan(self, owner: Owner, pet: Pet, tasks: list[Task]) -> DailyPlan:
        """Produce a DailyPlan for the day from the owner, pet, and candidate tasks."""
        raise NotImplementedError

    def _sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Return tasks ordered by priority (then duration) for greedy packing."""
        raise NotImplementedError
