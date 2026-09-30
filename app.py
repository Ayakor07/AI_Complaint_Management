# app.py
# ---------------------------------------------------------------
# AI-Enhanced Complaint Management and Service Quality
# Decision Support System  -  VERSION 1 (Streamlit foundation)
#
# This first version only shows the landing page and the layout.
# There is NO login, database, AI or analytics yet.
# ---------------------------------------------------------------

import streamlit as st  # Streamlit turns this Python file into a web app

# ---------------------------------------------------------------
# 1. PAGE SETTINGS
# ---------------------------------------------------------------
# set_page_config() must be the FIRST Streamlit command in the file.
# It sets the browser tab title, icon and page layout.
st.set_page_config(
    page_title="Complaint Management System",
    page_icon="🎓",
    layout="wide",  # use the full width of the browser
)

# ---------------------------------------------------------------
# 2. CUSTOM STYLING (CSS)
# ---------------------------------------------------------------
# Streamlit lets us add a little CSS to make the page look more
# professional. You do not need to understand CSS to use this;
# it only changes colours, spacing and card appearance.
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

        /* Cards for Student / Staff / Administrator */
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
    unsafe_allow_html=True,  # allows Streamlit to render our HTML/CSS
)

# ---------------------------------------------------------------
# 3. SIDEBAR
# ---------------------------------------------------------------
# Everything inside "with st.sidebar:" appears in the left panel.
with st.sidebar:
    st.title("🎓 Complaint System")
    st.caption(
        "AI-Enhanced Complaint Management and Service Quality Decision Support System")
    st.divider()

    # st.radio shows a list of options and remembers which one is chosen.
    # These are only PLACEHOLDERS for now. Real pages come later.
    selected_page = st.radio(
        "Navigation",
        ["Home", "Login", "Student Dashboard",
            "Staff Dashboard", "Admin Dashboard", "Reports"],
    )

    st.divider()
    st.caption("Final-Year Project Prototype • Version 1")

# ---------------------------------------------------------------
# 4. PLACEHOLDER MESSAGE
# ---------------------------------------------------------------
# If the user picks anything other than "Home", show a friendly
# "coming soon" note. The landing page still shows below it.
if selected_page != "Home":
    st.info(
        f"🚧 **{selected_page}** is a placeholder. This feature will be built in a later version.")

# ---------------------------------------------------------------
# 5. HERO / WELCOME SECTION
# ---------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <h1>AI-Enhanced Complaint Management and Service Quality Decision Support System</h1>
        <p>
            Welcome! This system helps the university receive, track and resolve
            complaints, and uses data insights to support better service-quality
            decisions for students, staff and management.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader("About the System")
st.write(
    "This platform manages university complaints from submission to resolution. "
    "Students can report problems, staff can respond and update progress, and "
    "administrators can monitor trends to improve services across the institution."
)

st.write("")  # empty line for spacing

# ---------------------------------------------------------------
# 6. THREE ROLE CARDS
# ---------------------------------------------------------------
st.subheader("Who Uses This System?")

# st.columns(3) splits the page into three equal side-by-side columns.
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
# 7. FOOTER
# ---------------------------------------------------------------
st.write("")
st.divider()
st.caption(
    "© 2026 University Complaint Management System • Final-Year Project Prototype")
