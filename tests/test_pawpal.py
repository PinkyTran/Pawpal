"""Tests for the PawPal+ scheduling system.

Run from the repo root with: pytest
"""

import pytest

from pawpal_system import DailyPlan, Owner, Pet, Priority, Scheduler, Task


# --- helpers ---------------------------------------------------------------

def make_owner(available_minutes, tasks_by_pet):
    """Build an Owner whose pets carry the given tasks.

    tasks_by_pet: list of (pet_name, [Task, ...]) pairs.
    """
    pets = [Pet(name, "dog", tasks=tasks) for name, tasks in tasks_by_pet]
    return Owner("Owner", available_minutes=available_minutes, pets=pets)


# --- Task ------------------------------------------------------------------

def test_rank_orders_high_above_medium_above_low():
    assert Task("a", 10, Priority.HIGH).rank() > Task("b", 10, Priority.MEDIUM).rank()
    assert Task("b", 10, Priority.MEDIUM).rank() > Task("c", 10, Priority.LOW).rank()


def test_task_rejects_non_positive_duration():
    with pytest.raises(ValueError):
        Task("bad", 0, Priority.HIGH)
    with pytest.raises(ValueError):
        Task("bad", -5, Priority.LOW)


def test_mark_complete_changes_status():
    """Task Completion: mark_complete() flips the task's status."""
    task = Task("Feeding", 10, Priority.HIGH)
    assert task.status == "pending"
    task.mark_complete()
    assert task.status == "complete"


def test_adding_task_increases_pet_task_count():
    """Task Addition: add_task() grows the pet's task list by one."""
    pet = Pet("Biscuit", "dog")
    assert len(pet.tasks) == 0
    pet.add_task(Task("Morning walk", 30, Priority.HIGH))
    assert len(pet.tasks) == 1


# --- Scheduler helpers -----------------------------------------------------

def test_collect_tasks_flattens_across_pets():
    owner = make_owner(
        100,
        [
            ("Biscuit", [Task("walk", 30, Priority.HIGH)]),
            ("Mochi", [Task("meds", 5, Priority.HIGH), Task("play", 15, Priority.LOW)]),
        ],
    )
    collected = Scheduler()._collect_tasks(owner)
    assert len(collected) == 3
    # each entry is a (pet, task) pair
    pets = {pet.name for pet, _ in collected}
    assert pets == {"Biscuit", "Mochi"}


def test_sort_tasks_by_priority_then_duration():
    tasks = [
        Task("low-short", 5, Priority.LOW),
        Task("high-long", 40, Priority.HIGH),
        Task("high-short", 10, Priority.HIGH),
        Task("med", 20, Priority.MEDIUM),
    ]
    pet = Pet("P", "dog")
    ordered = Scheduler()._sort_tasks([(pet, t) for t in tasks])
    titles = [t.title for _, t in ordered]
    # HIGH first (shorter before longer), then MEDIUM, then LOW
    assert titles == ["high-short", "high-long", "med", "low-short"]


def test_sort_is_stable_for_full_ties():
    """Same priority and duration -> original order is preserved (deterministic)."""
    pet = Pet("P", "dog")
    tasks = [Task("first", 10, Priority.HIGH), Task("second", 10, Priority.HIGH)]
    ordered = Scheduler()._sort_tasks([(pet, t) for t in tasks])
    assert [t.title for _, t in ordered] == ["first", "second"]


# --- build_plan ------------------------------------------------------------

def test_high_priority_scheduled_before_low():
    owner = make_owner(
        100,
        [("P", [Task("low", 10, Priority.LOW), Task("high", 10, Priority.HIGH)])],
    )
    plan = Scheduler().build_plan(owner)
    assert [i.task.title for i in plan.items] == ["high", "low"]


def test_tasks_over_budget_are_skipped_with_reason():
    owner = make_owner(
        20,
        [("P", [Task("fits", 20, Priority.HIGH), Task("toobig", 30, Priority.HIGH)])],
    )
    plan = Scheduler().build_plan(owner)
    assert [i.task.title for i in plan.items] == ["fits"]
    assert [i.task.title for i in plan.skipped] == ["toobig"]
    assert "30 min" in plan.skipped[0].reason and "0 min" in plan.skipped[0].reason


def test_greedy_fills_leftover_time_with_smaller_task():
    """A big task that doesn't fit is skipped, but a smaller later task still gets in."""
    owner = make_owner(
        25,
        [(
            "P",
            [
                Task("big", 20, Priority.MEDIUM),   # scheduled (5 left)
                Task("huge", 30, Priority.MEDIUM),  # skipped, doesn't fit
                Task("tiny", 5, Priority.MEDIUM),   # still fits in the leftover 5
            ],
        )],
    )
    plan = Scheduler().build_plan(owner)
    scheduled = [i.task.title for i in plan.items]
    assert "tiny" in scheduled
    assert [i.task.title for i in plan.skipped] == ["huge"]


def test_total_minutes_sums_scheduled_only():
    owner = make_owner(
        50,
        [("P", [Task("a", 20, Priority.HIGH), Task("b", 20, Priority.HIGH),
                Task("c", 40, Priority.LOW)])],
    )
    plan = Scheduler().build_plan(owner)
    assert plan.total_minutes == 40  # a + b; c skipped


def test_start_times_are_sequential_from_start_hour():
    # Equal durations -> stable order, so timing is back-to-back and unambiguous.
    owner = make_owner(
        60,
        [("P", [Task("a", 30, Priority.HIGH), Task("b", 30, Priority.HIGH)])],
    )
    plan = Scheduler(start_hour=8).build_plan(owner)
    assert plan.items[0].start_time == "08:00"
    assert plan.items[1].start_time == "08:30"


def test_zero_budget_skips_everything():
    owner = make_owner(0, [("P", [Task("a", 10, Priority.HIGH)])])
    plan = Scheduler().build_plan(owner)
    assert plan.items == []
    assert len(plan.skipped) == 1
    assert plan.total_minutes == 0


def test_owner_with_no_tasks_produces_empty_plan():
    owner = Owner("Solo", available_minutes=100, pets=[Pet("P", "dog")])
    plan = Scheduler().build_plan(owner)
    assert plan.items == [] and plan.skipped == []
    assert isinstance(plan, DailyPlan)


# --- explain ---------------------------------------------------------------

def test_explain_names_pet_and_reports_budget():
    owner = make_owner(30, [("Biscuit", [Task("Morning walk", 30, Priority.HIGH)])])
    text = Scheduler().build_plan(owner).explain()
    assert "Morning walk" in text
    assert "Biscuit" in text
    assert "budget: 30 min" in text
