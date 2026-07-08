import streamlit as st

from pawpal_system import Owner, Pet, Priority, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")
st.caption("Plan your pets' daily care around the time you actually have.")

PRIORITIES = ["high", "medium", "low"]
PRIORITY_ENUM = {"high": Priority.HIGH, "medium": Priority.MEDIUM, "low": Priority.LOW}

# --- Step 2: the session "vault" -------------------------------------------
# Streamlit re-runs this whole script on every interaction. If we created the
# Owner here unconditionally it would be reborn empty each time, losing all the
# pets and tasks. So we create it ONCE and keep the SAME instance in
# st.session_state (a dict-like store that survives reruns), checking whether
# it already exists before making a new one.
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=200)

owner = st.session_state.owner  # the persisted instance we mutate below

# --- owner + constraints ---------------------------------------------------
st.subheader("1. Owner & time budget")
col_a, col_b, col_c = st.columns(3)
with col_a:
    owner.name = st.text_input("Owner name", value=owner.name)
with col_b:
    owner.available_minutes = st.number_input(
        "Time available today (min)", min_value=0, max_value=1440,
        value=owner.available_minutes, step=5,
    )
with col_c:
    start_hour = st.number_input("Start hour", min_value=0, max_value=23, value=8)

st.divider()

# --- Step 3: add a pet -> Owner.add_pet() ----------------------------------
st.subheader("2. Pets")
with st.form("add_pet", clear_on_submit=True):
    pc1, pc2, pc3 = st.columns(3)
    with pc1:
        new_pet_name = st.text_input("Pet name", value="")
    with pc2:
        new_pet_species = st.selectbox("Species", ["dog", "cat", "other"])
    with pc3:
        new_pet_breed = st.text_input("Breed", value="")
    pc4, pc5 = st.columns(2)
    with pc4:
        new_pet_color = st.text_input("Color", value="")
    with pc5:
        new_pet_age = st.number_input("Age (years)", min_value=0, max_value=40, value=0)

    if st.form_submit_button("Add pet"):
        name = new_pet_name.strip()
        existing = {p.name for p in owner.pets}
        if not name:
            st.warning("Please enter a pet name.")
        elif name in existing:
            st.warning(f"You already have a pet named {name}.")
        else:
            # The method on the class handles the data; the rerun after this
            # submit re-reads owner.pets and shows the new pet automatically.
            owner.add_pet(
                Pet(
                    name=name,
                    species=new_pet_species,
                    breed=new_pet_breed,
                    color=new_pet_color,
                    age=int(new_pet_age),
                )
            )

if not owner.pets:
    st.info("Add at least one pet to get started.")

# --- Step 3: add a task -> Pet.add_task() ----------------------------------
if owner.pets:
    st.subheader("3. Tasks")
    with st.form("add_task", clear_on_submit=True):
        tc1, tc2, tc3 = st.columns([2, 2, 1])
        with tc1:
            task_pet_name = st.selectbox("For pet", [p.name for p in owner.pets])
        with tc2:
            task_title = st.text_input("Task", value="Morning walk")
        with tc3:
            task_duration = st.number_input("Min", min_value=1, max_value=240, value=20)
        tc4, tc5 = st.columns(2)
        with tc4:
            task_priority = st.selectbox("Priority", PRIORITIES, index=0)
        with tc5:
            task_frequency = st.selectbox("Repeats", ["once", "daily", "weekly"], index=0)

        if st.form_submit_button("Add task") and task_title.strip():
            pet = next(p for p in owner.pets if p.name == task_pet_name)
            pet.add_task(
                Task(
                    title=task_title.strip(),
                    duration_minutes=int(task_duration),
                    priority=PRIORITY_ENUM[task_priority],
                    frequency=task_frequency,
                )
            )

    # show current pets + their tasks (read straight off the Owner object)
    for pet in owner.pets:
        with st.expander(f"🐾 {pet.name} ({pet.species}) — {len(pet.tasks)} task(s)", expanded=True):
            traits = []
            if pet.breed:
                traits.append(f"Breed: {pet.breed}")
            if pet.color:
                traits.append(f"Color: {pet.color}")
            if pet.age:
                traits.append(f"Age: {pet.age} yr")
            if traits:
                st.caption(" · ".join(traits))

            if pet.tasks:
                for idx, t in enumerate(pet.tasks):
                    r1, r2, r3 = st.columns([5, 3, 2])
                    done = t.status == "complete"
                    title = f"~~{t.title}~~" if done else t.title
                    r1.markdown(f"{'✅' if done else '⬜'} {title}")
                    meta = f"{t.duration_minutes} min · {t.priority.value}"
                    if t.frequency != "once":
                        meta += f" · 🔁 {t.frequency}"
                    r2.caption(meta)
                    if done:
                        r3.caption("done")
                    elif r3.button("Mark done", key=f"done_{pet.name}_{idx}"):
                        # completes the task; recurring tasks auto-spawn the next one
                        nxt = pet.complete_task(t)
                        if nxt is not None:
                            st.toast(f"Next {t.title} scheduled for {nxt.due_date}")
                        st.rerun()
                if st.button(f"Clear {pet.name}'s tasks", key=f"clear_{pet.name}"):
                    pet.tasks.clear()
                    st.rerun()
            else:
                st.caption("No tasks yet.")

st.divider()

# --- generate the plan -----------------------------------------------------
st.subheader("4. Today's plan")
st.caption("Tasks are scheduled highest-priority first and packed into your time budget.")

if st.button("Generate schedule", type="primary", disabled=not owner.pets):
    # The Owner already holds everything the scheduler needs.
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
