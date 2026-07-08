"""PawPal+ core system.

Implements the priority + time-budget design from diagrams/uml.mmd: an owner's
pets carry care tasks, and the Scheduler fits them into the owner's time budget.
"""

from __future__ import annotations

from enum import Enum


class Priority(Enum):
    """How important a task is. Drives ranking in the scheduler."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Owner:
    """The pet owner: their time budget, preferences, and the pets they care for."""

    def __init__(
        self,
        name: str,
        available_minutes: int,
        preferences: list[str] | None = None,
        pets: list[Pet] | None = None,
    ):
        """Create an owner with a daily time budget, preferences, and pets."""
        self.name = name
        self.available_minutes = available_minutes
        self.preferences = preferences if preferences is not None else []
        self.pets = pets if pets is not None else []


class Pet:
    """A pet the owner cares for, along with the tasks to be done for it."""

    def __init__(self, name: str, species: str, breed: str = "", tasks: list[Task] | None = None):
        """Create a pet with its species, breed, and starting task list."""
        self.name = name
        self.species = species
        self.breed = breed
        self.tasks = tasks if tasks is not None else []

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet."""
        self.tasks.append(task)


class Task:
    """One care activity: what it is, how long it takes, how important."""

    def __init__(self, title: str, duration_minutes: int, priority: Priority, category: str = ""):
        """Create a care task; raises ValueError if the duration is not positive."""
        if duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")
        self.title = title
        self.duration_minutes = duration_minutes
        self.priority = priority
        self.category = category
        self.status = "pending"

    def rank(self) -> int:
        """Return a sortable integer for this task's priority (higher = more important)."""
        return {Priority.HIGH: 3, Priority.MEDIUM: 2, Priority.LOW: 1}[self.priority]

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.status = "complete"


class PlanItem:
    """A scheduler decision about a single task: which pet, included/skipped, when, and why."""

    def __init__(self, task: Task, pet: Pet, start_time: str, included: bool, reason: str):
        """Record one scheduling decision: the task, its pet, time, and reason."""
        self.task = task
        self.pet = pet
        self.start_time = start_time
        self.included = included
        self.reason = reason


class DailyPlan:
    """The result of scheduling across all of an owner's pets: what got in, what got skipped."""

    def __init__(
        self,
        owner: Owner,
        items: list[PlanItem] | None = None,
        skipped: list[PlanItem] | None = None,
        total_minutes: int = 0,
    ):
        """Hold the scheduled and skipped items for an owner's day."""
        self.owner = owner
        self.items = items if items is not None else []
        self.skipped = skipped if skipped is not None else []
        self.total_minutes = total_minutes

    def explain(self) -> str:
        """Return a human-readable explanation of the plan and its choices."""
        lines = [
            f"Daily plan for {self.owner.name} "
            f"(budget: {self.owner.available_minutes} min, used: {self.total_minutes} min)",
        ]

        lines.append("")
        if self.items:
            lines.append("Scheduled:")
            for item in self.items:
                t = item.task
                lines.append(
                    f"  {item.start_time} — {t.title} for {item.pet.name} "
                    f"({t.duration_minutes} min) [priority: {t.priority.value}] — {item.reason}"
                )
        else:
            lines.append("Scheduled: nothing fit in the available time.")

        if self.skipped:
            lines.append("")
            lines.append("Skipped:")
            for item in self.skipped:
                t = item.task
                lines.append(
                    f"  {t.title} for {item.pet.name} "
                    f"({t.duration_minutes} min) [priority: {t.priority.value}] — {item.reason}"
                )

        return "\n".join(lines)


class Scheduler:
    """Ranks tasks by priority, fits them into the owner's time budget, builds a DailyPlan."""

    def __init__(self, start_hour: int = 8):
        """Create a scheduler that starts placing tasks at start_hour."""
        self.start_hour = start_hour

    def build_plan(self, owner: Owner) -> DailyPlan:
        """Greedily fit the owner's ranked pet tasks into their time budget."""
        ranked = self._sort_tasks(self._collect_tasks(owner))

        remaining = owner.available_minutes
        cursor = self.start_hour * 60  # minutes since midnight
        items: list[PlanItem] = []
        skipped: list[PlanItem] = []
        used = 0

        for pet, task in ranked:
            if task.duration_minutes <= remaining:
                items.append(
                    PlanItem(
                        task=task,
                        pet=pet,
                        start_time=self._format_time(cursor),
                        included=True,
                        reason=f"{task.priority.value} priority, fits the remaining time",
                    )
                )
                cursor += task.duration_minutes
                remaining -= task.duration_minutes
                used += task.duration_minutes
            else:
                skipped.append(
                    PlanItem(
                        task=task,
                        pet=pet,
                        start_time="",
                        included=False,
                        reason=f"needs {task.duration_minutes} min but only {remaining} min left",
                    )
                )

        return DailyPlan(owner=owner, items=items, skipped=skipped, total_minutes=used)

    def _collect_tasks(self, owner: Owner) -> list[tuple[Pet, Task]]:
        """Flatten every (pet, task) pair across all of the owner's pets."""
        return [(pet, task) for pet in owner.pets for task in pet.tasks]

    def _sort_tasks(self, pet_tasks: list[tuple[Pet, Task]]) -> list[tuple[Pet, Task]]:
        """Return (pet, task) pairs by priority desc then duration asc (stable order)."""
        return sorted(
            pet_tasks,
            key=lambda pt: (-pt[1].rank(), pt[1].duration_minutes),
        )

    @staticmethod
    def _format_time(minutes_since_midnight: int) -> str:
        """Format minutes-since-midnight as 'HH:MM' (wraps past 24h)."""
        hours, minutes = divmod(minutes_since_midnight % (24 * 60), 60)
        return f"{hours:02d}:{minutes:02d}"
