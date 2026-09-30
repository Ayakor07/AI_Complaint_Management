# app.py
# ---------------------------------------------------------------
# AI-Enhanced Complaint Management and Service Quality
# Decision Support System  -  VERSION 4 (Student: Submit Complaint)
#
# This version adds:
#   - a working "Submit Complaint" form on the Student dashboard
#   - a "My Complaints" table showing only the logged-in student's complaints
# Login still uses the demo accounts below.
# There is still NO AI or analytics.
# ---------------------------------------------------------------

import streamlit as st  # Streamlit turns this Python file into a web app
import pandas as pd     # NEW: Pandas builds the "My Complaints" table

# CHANGED: we now also import the functions needed for complaints
from utils.database import (
    initialize_database,
    get_user_by_email,
    add_complaint,
    get_complaints,
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

# NEW: the choices shown in the complaint form dropdowns.
COMPLAINT_CATEGORIES = [
    "Academic", "IT / Network", "Library", "Hostel",
    "Facilities", "Finance", "Transportation", "Other",
]
COMPLAINT_PRIORITIES = ["Low", "Medium", "High"]

# NEW: the starting value of every field in the complaint form.
# The keys (left side) are also the widget keys used in the form below.
COMPLAINT_FORM_DEFAULTS = {
    "complaint_title": "",
    "complaint_description": "",
    "complaint_category": COMPLAINT_CATEGORIES[0],
    "complaint_location": "",
    "complaint_priority": "Medium",
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


# NEW: runs when the student presses "Submit Complaint".
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
# CHANGED: the Student dashboard now has a real form and table.
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

    st.divider()

    # ----- Section 3: still a placeholder ---------------------------
    placeholder_section(
        "🔎", "Complaint Status",
        "Students will track progress, read staff responses and view AI analysis.",
    )


def show_staff_dashboard():
    show_hero(f"Welcome back, {st.session_state.user_name}!")
    st.header("Staff Dashboard")

    col1, col2, col3 = st.columns(3)
    with col1:
        placeholder_section("📥", "Assigned Complaints",
                            "Staff will see the complaints assigned to them.")
    with col2:
        placeholder_section(
            "🔄", "Update Status", "Staff will change a complaint to Open, In Progress or Resolved.")
    with col3:
        placeholder_section("💬", "Respond to Complaint",
                            "Staff will write a reply to the student.")


def show_admin_dashboard():
    show_hero(f"Welcome back, {st.session_state.user_name}!")
    st.header("Administrator Dashboard")

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
    st.caption("Final-Year Project Prototype • Version 4")

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
