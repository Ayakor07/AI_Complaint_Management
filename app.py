# app.py
# ---------------------------------------------------------------
# AI-Enhanced Complaint Management and Service Quality
# Decision Support System  -  VERSION 7 (Admin: Complaint Assignment)
#
# This version adds the Administrator "Complaint Assignment" section:
#   - see ALL complaints with their assigned staff member
#   - select a complaint and view its details
#   - assign it (or reassign it) to a Staff user
# Login still uses the demo accounts below.
# There is still NO AI or analytics.
# ---------------------------------------------------------------

import streamlit as st  # Streamlit turns this Python file into a web app
import pandas as pd     # Pandas builds the complaint tables

# CHANGED: we now also import get_users_by_role and assign_complaint
from utils.database import (
    initialize_database,
    get_user_by_email,
    get_user_by_id,
    get_users_by_role,
    add_complaint,
    get_complaints,
    get_complaint_by_id,
    update_complaint_status,
    assign_complaint,
    add_response,
    get_responses,
)

# ---------------------------------------------------------------
# 1. PAGE SETTINGS
# ---------------------------------------------------------------
# set_page_config() must be the FIRST Streamlit command in the file.
st.set_page_config(
    page_title="Complaint Management System",
    page_icon="🎓",
    layout="wide",
)

# ---------------------------------------------------------------
# 1b. DATABASE SETUP
# ---------------------------------------------------------------
# @st.cache_resource makes Streamlit run this function only ONCE per
# server start instead of on every click. Inside, initialize_database()
# creates the tables and demo users if they do not exist yet.


@st.cache_resource(show_spinner=False)
def setup_database():
    initialize_database()
    return True


setup_database()

# ---------------------------------------------------------------
# 2. CUSTOM STYLING (CSS)
# ---------------------------------------------------------------
st.markdown(
    """
    <style>
        /* Big banner at the top of the page */
        .hero {
            background: linear-gradient(135deg, #1e3a8a, #2563eb);
            padding: 2.2rem 2rem;
            border-radius: 14px;
            color: white;
            margin-bottom: 1.5rem;
        }
        .hero h1 {
            color: white;
            font-size: 2rem;
            margin: 0 0 0.6rem 0;
            line-height: 1.3;
        }
        .hero p {
            color: #dbeafe;
            font-size: 1.05rem;
            margin: 0;
        }

        /* Cards for roles and dashboard sections */
        .card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-top: 5px solid #2563eb;
            border-radius: 12px;
            padding: 1.4rem;
            height: 100%;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
        }
        .card h3 {
            color: #1e3a8a;
            margin-top: 0;
        }
        .card p, .card li {
            color: #374151;
            font-size: 0.95rem;
        }
        .card ul {
            padding-left: 1.2rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------
# 3. DEMO USER ACCOUNTS
# ---------------------------------------------------------------
# A dictionary stores each account. The KEY is the email address and
# the VALUE holds the password, display name and role.
# NOTE: Plain-text passwords are fine for a demo only. In a later
# stage, login will check the database instead.
DEMO_USERS = {
    "student@university.edu": {
        "password": "student123",
        "name": "Demo Student",
        "role": "Student",
    },
    "staff@university.edu": {
        "password": "staff123",
        "name": "Demo Staff",
        "role": "Staff",
    },
    "admin@university.edu": {
        "password": "admin123",
        "name": "Demo Administrator",
        "role": "Administrator",
    },
}

# The choices shown in the complaint form dropdowns.
COMPLAINT_CATEGORIES = [
    "Academic", "IT / Network", "Library", "Hostel",
    "Facilities", "Finance", "Transportation", "Other",
]
COMPLAINT_PRIORITIES = ["Low", "Medium", "High"]

# The statuses a staff member can choose from.
STATUS_OPTIONS = ["Pending", "In Progress", "Resolved"]

# The starting value of every field in the complaint form.
# The keys (left side) are also the widget keys used in the form below.
COMPLAINT_FORM_DEFAULTS = {
    "complaint_title": "",
    "complaint_description": "",
    "complaint_category": COMPLAINT_CATEGORIES[0],
    "complaint_location": "",
    "complaint_priority": "Medium",
}

# A small coloured icon shown next to each status.
STATUS_ICONS = {
    "Pending": "🟡",
    "In Progress": "🔵",
    "Resolved": "🟢",
}

# ---------------------------------------------------------------
# 4. SESSION STATE (the app's "memory")
# ---------------------------------------------------------------
# Streamlit re-runs this whole file on every click, so normal
# variables are forgotten. st.session_state keeps values between
# runs. We create the values only if they do not exist yet.
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = None
    st.session_state.user_name = None
    st.session_state.role = None


# ---------------------------------------------------------------
# 5. HELPER FUNCTIONS
# ---------------------------------------------------------------
def check_login(email, password):
    """Return the user's details if the email and password are correct,
    otherwise return None."""
    email = email.strip().lower()  # ignore extra spaces and capital letters
    user = DEMO_USERS.get(email)   # look up the email in our dictionary
    if user is not None and user["password"] == password:
        return {"email": email, "name": user["name"], "role": user["role"]}
    return None


def logout():
    """Clear the saved login details. Used by the Logout button."""
    st.session_state.logged_in = False
    st.session_state.user_email = None
    st.session_state.user_name = None
    st.session_state.role = None


def show_hero(message):
    """Show the blue banner with the project title and a short message."""
    st.markdown(
        f"""
        <div class="hero">
            <h1>AI-Enhanced Complaint Management and Service Quality Decision Support System</h1>
            <p>{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def placeholder_section(icon, title, description):
    """Show one card for a feature that will be built in a later stage."""
    st.markdown(
        f"""
        <div class="card">
            <h3>{icon} {title}</h3>
            <p>{description}</p>
            <p><em>🚧 Coming in a later version.</em></p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def handle_complaint_submit():
    """Validate the form, save the complaint to the database, then reset the form.

    This function is used as a CALLBACK: Streamlit runs it as soon as the
    button is pressed, BEFORE the page is redrawn. That is why we are allowed
    to change the form fields' values here (this is how we clear the form).
    The result message is stored in session_state so the page can show it
    after the redraw."""

    # Read what the student typed. .strip() removes extra spaces at the ends.
    title = st.session_state.complaint_title.strip()
    description = st.session_state.complaint_description.strip()
    location = st.session_state.complaint_location.strip()

    # 1. Required fields must not be empty.
    #    We return early WITHOUT clearing the form, so the student keeps their text.
    if not title or not description:
        st.session_state.complaint_feedback = (
            "error",
            "Please fill in both the Complaint Title and the Complaint Description.",
        )
        return

    # 2. Find the student's ID in the database using their login email.
    student = get_user_by_email(st.session_state.user_email)
    if student is None:
        st.session_state.complaint_feedback = (
            "error",
            "Your account was not found in the database. Please log out and log in again.",
        )
        return

    # 3. Save the complaint. add_complaint() automatically sets:
    #    status = 'Pending', created_at = now, resolved_at = NULL, assigned_staff = NULL.
    new_id = add_complaint(
        student_id=student["id"],
        title=title,
        description=description,
        category=st.session_state.complaint_category,
        location=location if location else None,  # empty location is saved as NULL
        priority=st.session_state.complaint_priority,
    )

    # 4. Reset every form field back to its starting value.
    for key, value in COMPLAINT_FORM_DEFAULTS.items():
        st.session_state[key] = value

    # 5. Remember a success message to display after the page redraws.
    st.session_state.complaint_feedback = (
        "success",
        f"✅ Complaint #{new_id} was submitted successfully. Its status is now Pending.",
    )


def show_complaint_details(complaint_id, student_id):
    """Display one complaint in full, but ONLY if it belongs to this student.

    complaint_id -> the complaint the student selected
    student_id   -> the logged-in student's database id"""

    # Load the complaint from the database.
    complaint = get_complaint_by_id(complaint_id)

    # SECURITY CHECK: the complaint must exist AND belong to this student.
    # If not, we show an error and stop (return) before showing anything.
    if complaint is None or complaint["student_id"] != student_id:
        st.error("⛔ You are not allowed to view this complaint.")
        return

    # ----- Work out the values that need a little logic -----------
    # Location is optional, so it may be empty (None).
    location = complaint["location"] if complaint["location"] else "Not specified"

    # assigned_staff holds a user id (a number) or None.
    # If it is set, look up that staff member's name.
    if complaint["assigned_staff"] is None:
        assigned_to = "Not assigned yet"
    else:
        staff_member = get_user_by_id(complaint["assigned_staff"])
        assigned_to = staff_member["name"] if staff_member else "Unknown staff member"

    # resolved_at is empty until the complaint is resolved.
    resolved_date = complaint["resolved_at"] if complaint["resolved_at"] else "Not resolved yet"

    # Pick an icon for the current status (fall back to a grey dot).
    status = complaint["status"]
    status_text = f"{STATUS_ICONS.get(status, '⚪')} {status}"

    # ----- Show the details in two columns -------------------------
    left, right = st.columns(2)
    with left:
        st.markdown(f"**Complaint ID:** #{complaint['id']}")
        st.markdown(f"**Title:** {complaint['title']}")
        st.markdown(f"**Category:** {complaint['category']}")
        st.markdown(f"**Location:** {location}")
    with right:
        st.markdown(f"**Priority:** {complaint['priority']}")
        st.markdown(f"**Current Status:** {status_text}")
        st.markdown(f"**Created Date:** {complaint['created_at']}")
        st.markdown(f"**Assigned Staff:** {assigned_to}")
        st.markdown(f"**Resolved Date:** {resolved_date}")

    # The description can be long, so it gets its own read-only box.
    # (disabled=True means the student can read it but not edit it.)
    st.text_area(
        "Description",
        value=complaint["description"],
        height=150,
        disabled=True,
        key=f"description_box_{complaint['id']}",
    )

    # ----- Staff responses ------------------------------------------
    st.markdown("##### 💬 Staff Responses")
    # each item includes 'staff_name'
    responses = get_responses(complaint["id"])

    if not responses:
        st.info("No staff response yet.")
    else:
        for reply in responses:
            staff_name = reply["staff_name"] if reply["staff_name"] else "Staff"
            st.markdown(f"**{staff_name}** • {reply['created_at']}")
            st.write(reply["response"])
            st.divider()


def handle_status_update(complaint_id, staff_id):
    """Change a complaint's status. Used as a CALLBACK for the Update Status button.

    Because a callback runs BEFORE the page is redrawn, the page will already
    show the new status. The result message is saved in session_state and
    displayed after the redraw.

    complaint_id -> the complaint being updated
    staff_id     -> the logged-in staff member's database id"""

    # SECURITY CHECK (again): only the assigned staff member may change it.
    complaint = get_complaint_by_id(complaint_id)
    if complaint is None or complaint["assigned_staff"] != staff_id:
        st.session_state.staff_feedback = (
            "error", "⛔ You are not allowed to update this complaint."
        )
        return

    # Read the status the staff member picked in the dropdown.
    # The dropdown's key is built from the complaint id (see below).
    new_status = st.session_state[f"status_select_{complaint_id}"]
    old_status = complaint["status"]

    if new_status == old_status:
        st.session_state.staff_feedback = (
            "info", f"The status is already {old_status}. Nothing was changed."
        )
        return

    # update_complaint_status() saves the new status AND keeps resolved_at consistent:
    #   -> becomes 'Resolved'        : resolved_at = current date/time
    #   -> moves away from 'Resolved': resolved_at is cleared (set to NULL)
    update_complaint_status(complaint_id, new_status)

    st.session_state.staff_feedback = (
        "success", f"✅ Status changed from {old_status} to {new_status}."
    )


def show_staff_complaint_details(complaint_id, staff_id):
    """Show a complaint's details, the status control, the response form and
    previous responses, but ONLY if the complaint is assigned to this staff member.

    complaint_id -> the complaint the staff member selected
    staff_id     -> the logged-in staff member's database id"""

    complaint = get_complaint_by_id(complaint_id)

    # SECURITY CHECK: the complaint must exist AND be assigned to this staff member.
    if complaint is None or complaint["assigned_staff"] != staff_id:
        st.error(
            "⛔ You are not allowed to view this complaint. It is not assigned to you.")
        return

    # Show the message left by the Update Status button (once).
    feedback = st.session_state.pop("staff_feedback", None)
    if feedback:
        message_type, message_text = feedback
        if message_type == "success":
            st.success(message_text)
        elif message_type == "error":
            st.error(message_text)
        else:
            st.info(message_text)

    # ----- Work out the values that need a little logic -----------
    location = complaint["location"] if complaint["location"] else "Not specified"

    # Look up the student's name from the student_id stored on the complaint.
    student = get_user_by_id(complaint["student_id"])
    student_text = f"{student['name']} (ID {student['id']})" if student else f"ID {complaint['student_id']}"

    status = complaint["status"]
    status_text = f"{STATUS_ICONS.get(status, '⚪')} {status}"

    # ----- Details in two columns ----------------------------------
    left, right = st.columns(2)
    with left:
        st.markdown(f"**Complaint ID:** #{complaint['id']}")
        st.markdown(f"**Title:** {complaint['title']}")
        st.markdown(f"**Category:** {complaint['category']}")
        st.markdown(f"**Location:** {location}")
    with right:
        st.markdown(f"**Priority:** {complaint['priority']}")
        st.markdown(f"**Status:** {status_text}")
        st.markdown(f"**Created Date:** {complaint['created_at']}")
        st.markdown(f"**Student:** {student_text}")

    st.text_area(
        "Description",
        value=complaint["description"],
        height=150,
        disabled=True,
        key=f"staff_description_box_{complaint['id']}",
    )

    # ----- Update Status -------------------------------------------
    st.markdown("##### 🔄 Update Status")
    col_select, col_button = st.columns([3, 1])
    with col_select:
        # The dropdown starts on the complaint's current status.
        # The key includes the complaint id so each complaint has its own dropdown.
        current_index = STATUS_OPTIONS.index(
            status) if status in STATUS_OPTIONS else 0
        st.selectbox(
            "New status",
            STATUS_OPTIONS,
            index=current_index,
            key=f"status_select_{complaint['id']}",
        )
    with col_button:
        st.write("")  # small spacer so the button lines up with the dropdown
        st.write("")
        # on_click runs handle_status_update(complaint_id, staff_id) when pressed.
        st.button(
            "Update Status",
            key=f"status_button_{complaint['id']}",
            on_click=handle_status_update,
            args=(complaint["id"], staff_id),
            use_container_width=True,
        )

    # ----- Write a Response ----------------------------------------
    st.markdown("##### ✍️ Respond to Complaint")

    # clear_on_submit=True empties the text box after the form is submitted.
    with st.form(f"response_form_{complaint['id']}", clear_on_submit=True):
        reply_text = st.text_area(
            "Write your response to the student",
            height=120,
            placeholder="Explain what action is being taken, or ask the student for more information.",
        )
        send_clicked = st.form_submit_button("Send Response")

    if send_clicked:
        if not reply_text.strip():
            st.error("Please write a response before sending.")
        else:
            # Save the reply. add_response() stores the current date/time itself.
            add_response(complaint["id"], staff_id, reply_text.strip())
            st.success(
                "✅ Your response was saved and the student can now see it.")

    # ----- Previous Responses --------------------------------------
    # This runs AFTER the form above, so a reply just sent appears immediately.
    st.markdown("##### 💬 Previous Responses")
    responses = get_responses(complaint["id"])

    if not responses:
        st.info("No responses have been sent for this complaint yet.")
    else:
        for reply in responses:
            staff_name = reply["staff_name"] if reply["staff_name"] else "Staff"
            st.markdown(f"**{staff_name}** • {reply['created_at']}")
            st.write(reply["response"])
            st.divider()


# NEW: runs when the administrator presses the Assign / Reassign button.
def handle_assignment(complaint_id):
    """Assign (or reassign) a complaint to the staff member chosen in the dropdown.
    Used as a CALLBACK, so it runs BEFORE the page is redrawn and the page
    will already show the new assignment.

    complaint_id -> the complaint being assigned"""

    # SECURITY CHECK: only an Administrator may assign complaints.
    if st.session_state.role != "Administrator":
        st.session_state.admin_feedback = (
            "error", "⛔ Only administrators can assign complaints."
        )
        return

    complaint = get_complaint_by_id(complaint_id)
    if complaint is None:
        st.session_state.admin_feedback = (
            "error", "That complaint no longer exists.")
        return

    # Read the staff member chosen in the dropdown (its key contains the complaint id).
    # The dropdown holds staff database ids, so this is a number.
    staff_id = st.session_state[f"assign_staff_{complaint_id}"]

    # Nothing to do if it is already assigned to that person.
    if complaint["assigned_staff"] == staff_id:
        st.session_state.admin_feedback = (
            "info", "This complaint is already assigned to that staff member."
        )
        return

    # Save the assignment. assign_complaint() also checks that the chosen
    # user really has the role "Staff".
    saved = assign_complaint(complaint_id, staff_id)

    if saved:
        staff_member = get_user_by_id(staff_id)
        st.session_state.admin_feedback = (
            "success",
            f"✅ Complaint #{complaint_id} is now assigned to {staff_member['name']}.",
        )
    else:
        st.session_state.admin_feedback = (
            "error", "The assignment could not be saved. Please try again."
        )


# NEW: the whole "Complaint Assignment" section of the Administrator dashboard.
def show_admin_assignment_section():
    """Show all complaints, the selected complaint's details, and the
    controls to assign or reassign it to a Staff user."""

    # SECURITY CHECK: this section is only for administrators.
    if st.session_state.role != "Administrator":
        st.error("⛔ Only administrators can access complaint assignment.")
        return

    st.subheader("🗂️ Complaint Assignment")

    # Load EVERY complaint in the database.
    complaints = get_complaints()

    if not complaints:
        st.info("There are no complaints in the system yet.")
        return

    # ----- Part 1: table of all complaints --------------------------
    # The table needs the staff member's NAME, but the complaint only stores an id.
    # We look each id up once and remember the name in a dictionary.
    staff_names = {}
    for c in complaints:
        staff_id = c["assigned_staff"]
        if staff_id is not None and staff_id not in staff_names:
            user = get_user_by_id(staff_id)
            staff_names[staff_id] = user["name"] if user else "Unknown"

    table = pd.DataFrame(complaints)
    # .map() replaces each id with the matching name. Missing ids become "Unassigned".
    table["assigned_name"] = table["assigned_staff"].map(
        staff_names).fillna("Unassigned")
    table = table[
        ["id", "title", "category", "priority",
            "status", "assigned_name", "created_at"]
    ].rename(columns={
        "id": "ID",
        "title": "Title",
        "category": "Category",
        "priority": "Priority",
        "status": "Status",
        "assigned_name": "Assigned Staff",
        "created_at": "Created",
    })
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.caption(f"{len(complaints)} complaint(s) in the system.")

    # ----- Part 2: choose a complaint -------------------------------
    st.markdown("#### 🔍 Select a Complaint")
    complaint_ids = [c["id"] for c in complaints]
    titles_by_id = {c["id"]: c["title"] for c in complaints}

    selected_id = st.selectbox(
        "Select a complaint",
        complaint_ids,
        format_func=lambda cid: f"#{cid} - {titles_by_id[cid]}",
        key="admin_selected_complaint",
    )

    # Reload the selected complaint fresh from the database, so the details
    # always show the latest assignment.
    complaint = get_complaint_by_id(selected_id)

    # Show the message left by the assignment button (once).
    feedback = st.session_state.pop("admin_feedback", None)
    if feedback:
        message_type, message_text = feedback
        if message_type == "success":
            st.success(message_text)
        elif message_type == "error":
            st.error(message_text)
        else:
            st.info(message_text)

    # ----- Part 3: details of the selected complaint -----------------
    location = complaint["location"] if complaint["location"] else "Not specified"

    if complaint["assigned_staff"] is None:
        current_staff_text = "Not assigned yet"
    else:
        current_staff = get_user_by_id(complaint["assigned_staff"])
        current_staff_text = current_staff["name"] if current_staff else "Unknown"

    status = complaint["status"]
    status_text = f"{STATUS_ICONS.get(status, '⚪')} {status}"

    left, right = st.columns(2)
    with left:
        st.markdown(f"**Complaint ID:** #{complaint['id']}")
        st.markdown(f"**Title:** {complaint['title']}")
        st.markdown(f"**Category:** {complaint['category']}")
        st.markdown(f"**Location:** {location}")
    with right:
        st.markdown(f"**Priority:** {complaint['priority']}")
        st.markdown(f"**Status:** {status_text}")
        st.markdown(f"**Created Date:** {complaint['created_at']}")
        st.markdown(f"**Currently Assigned To:** {current_staff_text}")

    st.text_area(
        "Description",
        value=complaint["description"],
        height=150,
        disabled=True,
        key=f"admin_description_box_{complaint['id']}",
    )

    # ----- Part 4: assign or reassign --------------------------------
    st.markdown("##### 👤 Assign to Staff")

    # ONLY users whose role is "Staff" are loaded, so nobody else can be chosen.
    staff_list = get_users_by_role("Staff")

    if not staff_list:
        st.warning(
            "There are no Staff users in the system to assign complaints to.")
        return

    staff_ids = [s["id"] for s in staff_list]
    # A label for each option, e.g. "Staff User (Administration)".
    staff_labels = {
        s["id"]: f"{s['name']} ({s['department']})" if s["department"] else s["name"]
        for s in staff_list
    }

    # Start the dropdown on the current staff member (if there is one),
    # otherwise on the first person in the list.
    current_id = complaint["assigned_staff"]
    default_index = staff_ids.index(
        current_id) if current_id in staff_ids else 0

    col_select, col_button = st.columns([3, 1])
    with col_select:
        st.selectbox(
            "Choose a staff member",
            staff_ids,
            index=default_index,
            format_func=lambda sid: staff_labels[sid],
            key=f"assign_staff_{complaint['id']}",
        )
    with col_button:
        st.write("")  # spacers so the button lines up with the dropdown
        st.write("")
        # The button says "Reassign" when the complaint already has a staff member.
        button_label = "Reassign Complaint" if complaint[
            "assigned_staff"] is not None else "Assign Complaint"
        st.button(
            button_label,
            key=f"assign_button_{complaint['id']}",
            on_click=handle_assignment,
            args=(complaint["id"],),
            use_container_width=True,
        )


# ---------------------------------------------------------------
# 6. LOGIN PAGE
# ---------------------------------------------------------------
def show_login_page():
    show_hero(
        "Welcome! This system helps the university receive, track and resolve "
        "complaints, and supports better service-quality decisions. "
        "Please log in to continue."
    )

    # Three columns: the middle one holds the login form, so it appears centred.
    left, middle, right = st.columns([1, 1.4, 1])

    with middle:
        st.subheader("🔐 Login")

        # st.form groups the inputs so the app only reacts when the
        # button is pressed (not on every keystroke).
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="name@university.edu")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button(
                "Login", use_container_width=True)

        # This block runs only after the Login button is pressed.
        if submitted:
            user = check_login(email, password)
            if user:
                # Save the login details in session_state...
                st.session_state.logged_in = True
                st.session_state.user_email = user["email"]
                st.session_state.user_name = user["name"]
                st.session_state.role = user["role"]
                # ...then re-run the app so the dashboard appears.
                st.rerun()
            else:
                st.error("Incorrect email or password. Please try again.")

        # Helpful for demonstrations: show the demo accounts.
        with st.expander("Demo accounts (for demonstration only)"):
            st.markdown(
                """
                | Role | Email | Password |
                |---|---|---|
                | Student | student@university.edu | student123 |
                | Staff | staff@university.edu | staff123 |
                | Administrator | admin@university.edu | admin123 |
                """
            )

    # The three role cards stay on the login page.
    st.write("")
    st.subheader("Who Uses This System?")
    col_student, col_staff, col_admin = st.columns(3)

    with col_student:
        st.markdown(
            """
            <div class="card">
                <h3>🧑‍🎓 Student</h3>
                <p>Report issues and follow their progress.</p>
                <ul>
                    <li>Submit a complaint</li>
                    <li>Track complaint status</li>
                    <li>View staff responses</li>
                    <li>View AI analysis</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_staff:
        st.markdown(
            """
            <div class="card">
                <h3>🧑‍💼 Staff</h3>
                <p>Handle and resolve assigned complaints.</p>
                <ul>
                    <li>View assigned complaints</li>
                    <li>Update complaint status</li>
                    <li>Respond to students</li>
                    <li>Use AI-suggested responses</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_admin:
        st.markdown(
            """
            <div class="card">
                <h3>🛡️ Administrator</h3>
                <p>Oversee complaints and service quality.</p>
                <ul>
                    <li>View and assign all complaints</li>
                    <li>Analyse trends and resolution rates</li>
                    <li>View AI management insights</li>
                    <li>Generate reports</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------
# 7. ROLE DASHBOARDS
# ---------------------------------------------------------------
def show_student_dashboard():
    show_hero(f"Welcome back, {st.session_state.user_name}!")
    st.header("Student Dashboard")

    # Give every form field its starting value the first time this page opens.
    for key, value in COMPLAINT_FORM_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # ----- Section 1: Submit Complaint ------------------------------
    st.subheader("📝 Submit Complaint")
    st.write("Describe your problem below. Fields marked with * are required.")

    with st.form("complaint_form"):
        # key="..." connects each widget to a value in st.session_state.
        st.text_input("Complaint Title *", key="complaint_title", max_chars=150,
                      placeholder="e.g. Wi-Fi not working in the library")
        st.text_area("Complaint Description *", key="complaint_description", height=180,
                     placeholder="Explain what happened, when it started and how it affects you.")

        col_category, col_priority = st.columns(2)
        with col_category:
            st.selectbox("Category", COMPLAINT_CATEGORIES,
                         key="complaint_category")
        with col_priority:
            st.selectbox("Priority", COMPLAINT_PRIORITIES,
                         key="complaint_priority")

        st.text_input("Location (optional)", key="complaint_location",
                      placeholder="e.g. Main Library, Block B Room 204")

        # on_click runs handle_complaint_submit() when the button is pressed.
        st.form_submit_button("Submit Complaint",
                              on_click=handle_complaint_submit)

    # Show the result message (once). .pop() reads the message AND removes it,
    # so it does not appear again on the next click.
    feedback = st.session_state.pop("complaint_feedback", None)
    if feedback:
        message_type, message_text = feedback
        if message_type == "success":
            st.success(message_text)
        else:
            st.error(message_text)

    st.divider()

    # ----- Section 2: My Complaints ---------------------------------
    st.subheader("📂 My Complaints")

    # Find the logged-in student's database ID, then load ONLY their complaints.
    student = get_user_by_email(st.session_state.user_email)
    complaints = get_complaints(student_id=student["id"]) if student else []

    if not complaints:
        st.info(
            "You have not submitted any complaints yet. Use the form above to submit your first one.")
    else:
        # Turn the list of complaints into a Pandas table, keep only the
        # columns we want, and give them friendly names.
        table = pd.DataFrame(complaints)[
            ["id", "title", "category", "priority", "status", "created_at"]
        ].rename(columns={
            "id": "ID",
            "title": "Title",
            "category": "Category",
            "priority": "Priority",
            "status": "Status",
            "created_at": "Created",
        })
        st.dataframe(table, use_container_width=True, hide_index=True)
        st.caption(f"You have submitted {len(complaints)} complaint(s).")

        # ----- Complaint Details ------------------------------------
        st.markdown("#### 🔍 Complaint Details")

        # The dropdown is built ONLY from this student's own complaints,
        # so another student's complaint can never appear in it.
        complaint_ids = [c["id"] for c in complaints]
        titles_by_id = {c["id"]: c["title"] for c in complaints}

        selected_id = st.selectbox(
            "Select a complaint to view its details",
            complaint_ids,
            # format_func decides how each id is DISPLAYED, e.g. "#3 - Wi-Fi not working"
            format_func=lambda cid: f"#{cid} - {titles_by_id[cid]}",
        )

        # This function loads the complaint, double-checks ownership and shows it.
        show_complaint_details(selected_id, student["id"])

    st.divider()

    # ----- Section 3: still a placeholder ---------------------------
    placeholder_section(
        "🤖", "AI Analysis",
        "Students will view the AI analysis of their complaints (category, sentiment and summary).",
    )


def show_staff_dashboard():
    show_hero(f"Welcome back, {st.session_state.user_name}!")
    st.header("Staff Dashboard")

    # Find the logged-in staff member's database ID using their login email.
    staff = get_user_by_email(st.session_state.user_email)
    if staff is None:
        st.error(
            "Your account was not found in the database. Please log out and log in again.")
        return

    # Load ONLY the complaints assigned to this staff member.
    complaints = get_complaints(assigned_staff=staff["id"])

    # ----- Section 1: Summary metrics -------------------------------
    st.subheader("📊 Staff Complaint Dashboard")

    # Count complaints by status/priority with simple list comprehensions.
    total = len(complaints)
    pending = len([c for c in complaints if c["status"] == "Pending"])
    in_progress = len([c for c in complaints if c["status"] == "In Progress"])
    resolved = len([c for c in complaints if c["status"] == "Resolved"])
    high_priority = len([c for c in complaints if c["priority"] == "High"])

    # Five equal columns, one metric card in each.
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Assigned Complaints", total)
    m2.metric("Pending", pending)
    m3.metric("In Progress", in_progress)
    m4.metric("Resolved", resolved)
    m5.metric("High Priority", high_priority)

    st.divider()

    # ----- Section 2: Assigned Complaints ---------------------------
    st.subheader("📥 Assigned Complaints")

    if not complaints:
        st.info(
            "No complaints are assigned to you yet. "
            "Complaints appear here once an administrator assigns them to you."
        )
        return  # nothing else to show, so stop here

    # Turn the list into a Pandas table with friendly column names.
    table = pd.DataFrame(complaints)[
        ["id", "title", "category", "priority", "status", "created_at"]
    ].rename(columns={
        "id": "ID",
        "title": "Title",
        "category": "Category",
        "priority": "Priority",
        "status": "Status",
        "created_at": "Created",
    })
    st.dataframe(table, use_container_width=True, hide_index=True)

    st.divider()

    # ----- Section 3: Complaint Details, Status and Responses -------
    st.subheader("🔍 Complaint Details")

    # The dropdown is built ONLY from this staff member's assigned complaints.
    complaint_ids = [c["id"] for c in complaints]
    titles_by_id = {c["id"]: c["title"] for c in complaints}

    selected_id = st.selectbox(
        "Select an assigned complaint",
        complaint_ids,
        format_func=lambda cid: f"#{cid} - {titles_by_id[cid]}",
        key="staff_selected_complaint",
    )

    # This function double-checks the assignment, then shows details,
    # the status control, the response form and previous responses.
    show_staff_complaint_details(selected_id, staff["id"])


# CHANGED: the Administrator dashboard now starts with Complaint Assignment.
def show_admin_dashboard():
    show_hero(f"Welcome back, {st.session_state.user_name}!")
    st.header("Administrator Dashboard")

    # The real feature: view all complaints and assign them to staff.
    show_admin_assignment_section()

    st.divider()

    # The remaining admin features are still placeholders.
    col1, col2, col3 = st.columns(3)
    with col1:
        placeholder_section("📊", "Complaint Analytics",
                            "Charts for trends, resolution rate and recurring issues.")
    with col2:
        placeholder_section(
            "👥", "User Management", "Administrators will manage student and staff accounts.")
    with col3:
        placeholder_section(
            "📄", "Reports", "Administrators will generate service-quality reports.")


# ---------------------------------------------------------------
# 8. SIDEBAR
# ---------------------------------------------------------------
with st.sidebar:
    st.title("🎓 Complaint System")
    st.caption(
        "AI-Enhanced Complaint Management and Service Quality Decision Support System")
    st.divider()

    if st.session_state.logged_in:
        # Show who is logged in.
        st.markdown(f"**👤 {st.session_state.user_name}**")
        st.caption(f"Role: {st.session_state.role}")
        st.caption(st.session_state.user_email)

        # on_click=logout runs our logout() function when the button is pressed.
        st.button("Logout", on_click=logout, use_container_width=True)
    else:
        st.info("Please log in to access your dashboard.")

    st.divider()
    st.caption("Final-Year Project Prototype • Version 7")

# ---------------------------------------------------------------
# 9. MAIN PAGE ROUTING
# ---------------------------------------------------------------
# Decide which page to show, based on whether the user is logged in
# and what role is stored in session_state.
if not st.session_state.logged_in:
    show_login_page()
elif st.session_state.role == "Student":
    show_student_dashboard()
elif st.session_state.role == "Staff":
    show_staff_dashboard()
elif st.session_state.role == "Administrator":
    show_admin_dashboard()

# ---------------------------------------------------------------
# 10. FOOTER
# ---------------------------------------------------------------
st.write("")
st.divider()
st.caption(
    "© 2026 University Complaint Management System • Final-Year Project Prototype")
