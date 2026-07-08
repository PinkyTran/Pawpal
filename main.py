"""PawPal+ demo script.

Builds an owner with two pets and several care tasks, runs the scheduler,
and prints "Today's Schedule" to the terminal. Run with: python main.py
"""

from pawpal_system import Owner, Pet, Priority, Scheduler, Task


def build_owner() -> Owner:
    """Create a sample owner with two pets and a few tasks each."""
    biscuit = Pet(
        name="Biscuit",
        species="dog",
        breed="Golden Retriever",
        tasks=[
            Task("Morning walk", duration_minutes=30, priority=Priority.HIGH),
            Task("Feeding", duration_minutes=10, priority=Priority.HIGH),
            Task("Enrichment puzzle", duration_minutes=20, priority=Priority.MEDIUM),
            Task("Evening walk", duration_minutes=30, priority=Priority.MEDIUM),
            Task("Training session", duration_minutes=20, priority=Priority.MEDIUM),
            Task("Grooming", duration_minutes=25, priority=Priority.LOW),
            Task("Bath", duration_minutes=40, priority=Priority.LOW),
        ],
    )

    mochi = Pet(
        name="Mochi",
        species="cat",
        breed="Tabby",
        tasks=[
            Task("Medication", duration_minutes=5, priority=Priority.HIGH),
            Task("Evening feeding", duration_minutes=10, priority=Priority.HIGH),
            Task("Litter box cleaning", duration_minutes=10, priority=Priority.MEDIUM),
            Task("Play session", duration_minutes=15, priority=Priority.LOW),
            Task("Window watching", duration_minutes=15, priority=Priority.LOW),
        ],
    )

    return Owner(name="Jordan", available_minutes=200, pets=[biscuit, mochi])


def main() -> None:
    owner = build_owner()
    plan = Scheduler(start_hour=8).build_plan(owner)

    print("=" * 48)
    print("Today's Schedule")
    print("=" * 48)
    print(plan.explain())


if __name__ == "__main__":
    main()
