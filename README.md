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

## 🖥️ Sample Output

Running `python main.py` builds an owner (Jordan) with two pets — Biscuit (dog) and
Mochi (cat) — and 12 care tasks, then prints the generated plan:

```
================================================
Today's Schedule
================================================
Daily plan for Jordan (budget: 200 min, used: 190 min)

Scheduled:
  08:00 — Medication for Mochi (5 min) [priority: high] — high priority, fits the remaining time
  08:05 — Feeding for Biscuit (10 min) [priority: high] — high priority, fits the remaining time
  08:15 — Evening feeding for Mochi (10 min) [priority: high] — high priority, fits the remaining time
  08:25 — Morning walk for Biscuit (30 min) [priority: high] — high priority, fits the remaining time
  08:55 — Litter box cleaning for Mochi (10 min) [priority: medium] — medium priority, fits the remaining time
  09:05 — Enrichment puzzle for Biscuit (20 min) [priority: medium] — medium priority, fits the remaining time
  09:25 — Training session for Biscuit (20 min) [priority: medium] — medium priority, fits the remaining time
  09:45 — Evening walk for Biscuit (30 min) [priority: medium] — medium priority, fits the remaining time
  10:15 — Play session for Mochi (15 min) [priority: low] — low priority, fits the remaining time
  10:30 — Window watching for Mochi (15 min) [priority: low] — low priority, fits the remaining time
  10:45 — Grooming for Biscuit (25 min) [priority: low] — low priority, fits the remaining time

Skipped:
  Bath for Biscuit (40 min) [priority: low] — needs 40 min but only 10 min left
```

Tasks are scheduled highest-priority first (ties broken by shorter duration), packed
back-to-back from 08:00 until the owner's time budget runs out. Here every HIGH and
MEDIUM task fits; among the LOW tasks, only **Bath** (40 min) is skipped because just
10 minutes remained — the plan explains that reason for every task.

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
collected 25 items

tests/test_pawpal.py .........................                          [100%]

============================== 25 passed in 0.02s ==============================
```

The suite covers ranking, sorting (including deterministic tie-breaking), the
time-budget cutoff and skip reasons, `mark_complete()`, `add_task()`, recurring
tasks (`next_occurrence()` / `complete_task()`, including month/year rollover),
and edge cases like a zero-minute budget and a pet with no tasks.

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
