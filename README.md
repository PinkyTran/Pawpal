# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🏗️ Classes

PawPal+ separates the domain model (in `pawpal_system.py`) from the UI (`app.py`):

| Class | Responsibility | Key attributes | Key methods |
|-------|----------------|----------------|-------------|
| `Priority` | Enum ranking a task's importance | `HIGH`, `MEDIUM`, `LOW` | — |
| `Owner` | The pet owner: time budget + pets | `name`, `available_minutes`, `preferences`, `pets` | `add_pet()`, `filter_tasks()` |
| `Pet` | A pet and its care tasks | `name`, `species`, `breed`, `color`, `age`, `tasks` | `add_task()`, `complete_task()` |
| `Task` | One care activity | `title`, `duration_minutes`, `priority`, `time`, `frequency`, `due_date`, `status` | `rank()`, `mark_complete()`, `next_occurrence()` |
| `PlanItem` | One scheduling decision | `task`, `pet`, `start_time`, `included`, `reason` | — |
| `DailyPlan` | The scheduled + skipped result | `owner`, `items`, `skipped`, `total_minutes` | `explain()` |
| `Scheduler` | Ranks and fits tasks across all pets | `start_hour` | `build_plan()`, `sort_by_time()`, `detect_conflicts()` |

Relationships: an `Owner` has many `Pet`s, each `Pet` owns many `Task`s, and the
`Scheduler` reads an `Owner` to produce a `DailyPlan` of `PlanItem`s. See
[`diagrams/uml_final.mmd`](diagrams/uml_final.mmd) for the full class diagram.

## 🖥️ Running the demo

```bash
python main.py
```

This builds an owner (Jordan) with two pets — Biscuit (dog) and Mochi (cat), plus a
third pet (Rex) for the recurrence demo — adds several care tasks (some out of time
order and some deliberately clashing), then exercises the scheduler, conflict
detection, sorting, filtering, and recurring tasks:

```
====================================================
Today's Schedule
====================================================
Daily plan for Jordan (budget: 120 min, used: 115 min)

Scheduled:
  08:00 — Medication for Mochi (5 min) [priority: high] — high priority, fits the remaining time
  08:05 — Feeding for Biscuit (10 min) [priority: high] — high priority, fits the remaining time
  08:15 — Breakfast for Mochi (10 min) [priority: high] — high priority, fits the remaining time
  08:25 — Morning walk for Biscuit (30 min) [priority: high] — high priority, fits the remaining time
  08:55 — Backyard potty for Biscuit (5 min) [priority: medium] — medium priority, fits the remaining time
  09:00 — Litter box cleaning for Mochi (10 min) [priority: medium] — medium priority, fits the remaining time
  09:10 — Evening walk for Biscuit (30 min) [priority: medium] — medium priority, fits the remaining time
  09:40 — Play session for Mochi (15 min) [priority: low] — low priority, fits the remaining time

Skipped:
  Grooming for Biscuit (25 min) [priority: low] — needs 25 min but only 5 min left

====================================================
Schedule Conflicts
====================================================
⚠️ Conflict at 07:30: 'Feeding' (Biscuit), 'Breakfast' (Mochi)
⚠️ Conflict at 08:00: 'Morning walk' (Biscuit), 'Backyard potty' (Biscuit)

Biscuit's tasks SORTED BY TIME:
  07:30 — Feeding (10 min) [high] status=pending
  08:00 — Morning walk (30 min) [high] status=pending
  08:00 — Backyard potty (5 min) [medium] status=pending
  13:00 — Grooming (25 min) [low] status=pending
  18:00 — Evening walk (30 min) [medium] status=pending

====================================================
Recurring Tasks
====================================================
Before completing anything, Rex has 2 task(s).
  Completed 'Daily meds' (daily) -> next due: 2026-07-08
  Completed 'Weekly bath' (weekly) -> next due: 2026-07-14
After completing them, Rex has 4 task(s) (the auto-created next occurrences).
```

Tasks are scheduled highest-priority first (ties broken by shorter duration), packed
back-to-back from 08:00 until the budget runs out — here **Grooming** is skipped
because only 5 minutes remained. Conflict detection then flags same-time clashes
(both within one pet and across pets), `sort_by_time()` reorders the out-of-order
tasks, and completing a `daily`/`weekly` task auto-spawns its next occurrence.

*(Output above is trimmed slightly; the filtering section is omitted for brevity.)*

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
============================= test session starts ==============================
platform darwin -- Python 3.13.7, pytest-9.1.1, pluggy-1.6.0
rootdir: /Users/trang/Documents/AI101/Pawpal
collected 42 items

tests/test_pawpal.py ..........................................          [100%]

============================== 42 passed in 0.02s ==============================
```

The 42 tests cover ranking, sorting by priority-then-duration (including
deterministic tie-breaking), chronological `sort_by_time()` (untimed tasks last,
no mutation), filtering by status/pet, conflict detection (same-pet and cross-pet),
the time-budget cutoff and skip reasons, editing a task in place (`Task.update()`),
`mark_complete()`, `add_task()`, recurring tasks (`next_occurrence()` /
`complete_task()`, including month/year rollover), the "today only" planning filter
(completed and future-dated occurrences excluded), and edge cases like a zero-minute
budget, an owner with no pets, and a pet with no tasks.

## 📐 Smarter Scheduling

Beyond building a basic plan, PawPal+ implements several scheduling behaviors.
Each is a named method so it can be tested and reused independently of the UI.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Priority + time-budget planning | `Scheduler.build_plan()`, `Task.rank()`, `Scheduler._sort_tasks()` | Ranks tasks by priority (HIGH→LOW) then shorter duration first, packs them back-to-back from `start_hour`, and skips any task that doesn't fit the remaining budget (recording the reason on its `PlanItem`) |
| Sorting by time of day | `Scheduler.sort_by_time()` | Returns tasks ordered by their `"HH:MM"` time using a lambda key; untimed tasks sort last via a `"99:99"` sentinel. Does not mutate the input |
| Filtering | `Owner.filter_tasks(status, pet_name)` | Returns tasks filtered by completion status and/or pet name; either filter is optional, so no arguments returns everything |
| Conflict detection | `Scheduler.detect_conflicts()` | Groups all timed tasks by their `"HH:MM"` slot in one O(n) pass and returns a warning string for any slot claimed by 2+ tasks. Catches same-pet **and** cross-pet clashes, and returns warnings as data instead of raising |
| Recurring tasks | `Task.next_occurrence()`, `Pet.complete_task()` | Completing a `daily`/`weekly` task auto-creates the next occurrence, advancing the due date with `timedelta` (handles month/year rollover). The follow-up starts `pending` |

### Details

**Sorting** — `sort_by_time()` relies on the fact that zero-padded 24-hour
strings sort chronologically as plain text, so the key is simply
`lambda t: t.time or "99:99"`.

**Filtering** — `filter_tasks()` walks every pet's task list and keeps a task
only if it matches all supplied filters. `owner.filter_tasks(status="pending")`,
`owner.filter_tasks(pet_name="Mochi")`, or both together.

**Conflict detection** — `detect_conflicts()` uses a *lightweight* strategy: it
never raises. It returns a list like
`["⚠️ Conflict at 08:00: 'Morning walk' (Biscuit), 'Backyard potty' (Biscuit)"]`,
leaving the caller (CLI or Streamlit) to decide how to display it.

**Recurring tasks** — because a `Task` doesn't hold a reference to its `Pet`,
the recurrence is spawned by `Pet.complete_task()` (which owns the task list),
while `Task.next_occurrence()` does the pure date math. A `once` task returns
`None` and nothing is spawned.

## 📸 Demo Walkthrough

Launch the app with `streamlit run app.py`, then:

1. **Set the owner and time budget** — enter the owner's name, how many minutes are available today (e.g. 200), and the hour the day starts (e.g. 8).
2. **Add pets** — fill in a pet's name, species, breed, color, and age, then click **Add pet**. Repeat for each pet; they persist in the session as you go.
3. **Add tasks to a pet** — pick a pet, type a task (e.g. "Morning walk"), set its duration and priority, and click **Add task**. Each pet's tasks appear in its expander.
4. **Mark tasks complete** — click **Mark done** next to any task to flip its status (the title gets struck through).
5. **Generate the schedule** — click **Generate schedule** to see the scheduled tasks with times, the skipped tasks with reasons, and an expandable "Why this plan?" explanation.

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
