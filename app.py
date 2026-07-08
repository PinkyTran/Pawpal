import streamlit as st

from pawpal_system import Owner, Pet, Priority, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Plan your pets' daily care around the time you actually have.")

# --- session state ---------------------------------------------------------
# Pets are stored as plain dicts so the widgets can edit them freely; the
# pawpal_system objects are built fresh each time a plan is generated.
if "pets" not in st.session_state:
    st.session_state.pets = {}  # name -> {"species", "breed", "tasks": [ {..} ]}

PRIORITIES = ["high", "medium", "low"]
PRIORITY_ENUM = {"high": Priority.HIGH, "medium": Priority.MEDIUM, "low": Priority.LOW}

# --- owner + constraints ---------------------------------------------------
st.subheader("1. Owner & time budget")
col_a, col_b, col_c = st.columns(3)
with col_a:
    owner_name = st.text_input("Owner name", value="Jordan")
with col_b:
    available_minutes = st.number_input(
        "Time available today (min)", min_value=0, max_value=1440, value=200, step=5
    )
with col_c:
    start_hour = st.number_input("Start hour", min_value=0, max_value=23, value=8)

st.divider()

# --- add a pet -------------------------------------------------------------
st.subheader("2. Pets")
with st.form("add_pet", clear_on_submit=True):
    pc1, pc2, pc3 = st.columns(3)
    with pc1:
        new_pet_name = st.text_input("Pet name", value="")
    with pc2:
        new_pet_species = st.selectbox("Species", ["dog", "cat", "other"])
    with pc3:
        new_pet_breed = st.text_input("Breed (optional)", value="")
    if st.form_submit_button("Add pet") and new_pet_name.strip():
        st.session_state.pets.setdefault(
            new_pet_name.strip(),
            {"species": new_pet_species, "breed": new_pet_breed, "tasks": []},
        )

if not st.session_state.pets:
    st.info("Add at least one pet to get started.")

# --- add tasks to a pet ----------------------------------------------------
if st.session_state.pets:
    st.subheader("3. Tasks")
    with st.form("add_task", clear_on_submit=True):
        tc1, tc2, tc3, tc4 = st.columns([2, 2, 1, 1])
        with tc1:
            task_pet = st.selectbox("For pet", list(st.session_state.pets.keys()))
        with tc2:
            task_title = st.text_input("Task", value="Morning walk")
        with tc3:
            task_duration = st.number_input("Min", min_value=1, max_value=240, value=20)
        with tc4:
            task_priority = st.selectbox("Priority", PRIORITIES, index=0)
        if st.form_submit_button("Add task") and task_title.strip():
            st.session_state.pets[task_pet]["tasks"].append(
                {
                    "title": task_title.strip(),
                    "duration_minutes": int(task_duration),
                    "priority": task_priority,
                }
            )

    # show current pets + tasks, with a way to clear each pet's tasks
    for name, info in st.session_state.pets.items():
        with st.expander(f"🐾 {name} ({info['species']}) — {len(info['tasks'])} task(s)", expanded=True):
            if info["tasks"]:
                st.table(info["tasks"])
                if st.button(f"Clear {name}'s tasks", key=f"clear_{name}"):
                    info["tasks"] = []
                    st.rerun()
            else:
                st.caption("No tasks yet.")

st.divider()

# --- generate the plan -----------------------------------------------------
st.subheader("4. Today's plan")
st.caption("Tasks are scheduled highest-priority first and packed into your time budget.")

if st.button("Generate schedule", type="primary", disabled=not st.session_state.pets):
    pets = [
        Pet(
            name=name,
            species=info["species"],
            breed=info["breed"],
            tasks=[
                Task(
                    title=t["title"],
                    duration_minutes=t["duration_minutes"],
                    priority=PRIORITY_ENUM[t["priority"]],
                )
                for t in info["tasks"]
            ],
        )
        for name, info in st.session_state.pets.items()
    ]
    owner = Owner(name=owner_name, available_minutes=int(available_minutes), pets=pets)
    plan = Scheduler(start_hour=int(start_hour)).build_plan(owner)

    m1, m2, m3 = st.columns(3)
    m1.metric("Time used", f"{plan.total_minutes} min")
    m2.metric("Scheduled", len(plan.items))
    m3.metric("Skipped", len(plan.skipped))

    if plan.items:
        st.markdown("#### ✅ Scheduled")
        st.table(
            [
                {
                    "Time": i.start_time,
                    "Task": i.task.title,
                    "Pet": i.pet.name,
                    "Min": i.task.duration_minutes,
                    "Priority": i.task.priority.value,
                }
                for i in plan.items
            ]
        )
    else:
        st.warning("Nothing fit in the available time. Try increasing your time budget.")

    if plan.skipped:
        st.markdown("#### ⏭️ Skipped (ran out of time)")
        st.table(
            [
                {
                    "Task": i.task.title,
                    "Pet": i.pet.name,
                    "Min": i.task.duration_minutes,
                    "Priority": i.task.priority.value,
                    "Why": i.reason,
                }
                for i in plan.skipped
            ]
        )

    with st.expander("Why this plan? (full explanation)"):
        st.code(plan.explain(), language="text")
