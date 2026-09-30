# utils/database.py
# ---------------------------------------------------------------
# Reusable database functions for the Complaint Management System.
# Uses sqlite3, which is built into Python (nothing to install).
#
# Every other file (app.py, later pages) will import functions
# from here instead of writing SQL themselves.
# ---------------------------------------------------------------

import sqlite3
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------
# DATABASE LOCATION
# ---------------------------------------------------------------
# __file__ is this file (utils/database.py). We go up one folder to
# the project root, then into the "database" folder. Building the
# path this way works no matter where you run the app from.
DB_PATH = Path(__file__).resolve().parent.parent / \
    "database" / "complaint_system.db"


def _now():
    """Return the current date and time as text, e.g. '2026-09-30 14:05:00'.
    SQLite has no real date type, so we store dates as text."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------
# CONNECTION
# ---------------------------------------------------------------
def get_connection():
    """Open a connection to the SQLite database file."""
    DB_PATH.parent.mkdir(
        parents=True, exist_ok=True)  # make sure the folder exists
    conn = sqlite3.connect(DB_PATH)
    # row_factory lets us read columns by name: row["email"] instead of row[2]
    conn.row_factory = sqlite3.Row
    # SQLite ignores FOREIGN KEY rules unless we switch them on.
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---------------------------------------------------------------
# CREATE TABLES + DEMO USERS
# ---------------------------------------------------------------
def initialize_database():
    """Create the four tables (if missing) and add the demo users.
    It is safe to call many times: it never deletes or duplicates data."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            email      TEXT UNIQUE NOT NULL,
            password   TEXT NOT NULL,
            role       TEXT NOT NULL,
            department TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id     INTEGER NOT NULL,
            title          TEXT NOT NULL,
            description    TEXT NOT NULL,
            category       TEXT,
            location       TEXT,
            priority       TEXT DEFAULT 'Medium',
            sentiment      TEXT,
            status         TEXT DEFAULT 'Pending',
            assigned_staff INTEGER,
            created_at     TEXT NOT NULL,
            resolved_at    TEXT,
            FOREIGN KEY(student_id)     REFERENCES users(id),
            FOREIGN KEY(assigned_staff) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS responses (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id INTEGER NOT NULL,
            staff_id     INTEGER NOT NULL,
            response     TEXT NOT NULL,
            created_at   TEXT NOT NULL,
            FOREIGN KEY(complaint_id) REFERENCES complaints(id),
            FOREIGN KEY(staff_id)     REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ai_analysis (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id       INTEGER NOT NULL,
            category           TEXT,
            sentiment          TEXT,
            priority           TEXT,
            confidence         REAL,
            summary            TEXT,
            suggested_response TEXT,
            FOREIGN KEY(complaint_id) REFERENCES complaints(id)
        )
    """)

    conn.commit()
    conn.close()

    # Add the demo users. add_user() skips an email that already exists,
    # so running this again will not create duplicates.
    add_user("Student User", "student@university.edu",
             "student123", "Student", "General")
    add_user("Staff User", "staff@university.edu",
             "staff123", "Staff", "Administration")
    add_user("Admin User", "admin@university.edu",
             "admin123", "Administrator", "Administration")


# ---------------------------------------------------------------
# USERS
# ---------------------------------------------------------------
def add_user(name, email, password, role, department=None):
    """Add a new user. Returns the new user's id, or None if the email
    already exists.
    NOTE: passwords are stored as plain text because this is a demo.
    A real system would store a hashed password instead."""
    conn = get_connection()
    try:
        # The ? marks are placeholders. SQLite fills them in safely,
        # which protects against SQL injection. Always use them.
        cursor = conn.execute(
            "INSERT INTO users (name, email, password, role, department) VALUES (?, ?, ?, ?, ?)",
            (name, email.strip().lower(), password, role, department),
        )
        conn.commit()
        return cursor.lastrowid  # the id SQLite gave the new row
    except sqlite3.IntegrityError:
        # The email column is UNIQUE, so a duplicate email raises this error.
        return None
    finally:
        conn.close()


def get_user_by_email(email):
    """Find one user by email. Returns a dictionary, or None if not found."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?", (email.strip().lower(),)
    ).fetchone()
    conn.close()
    # dict(row) turns the row into a normal dictionary
    return dict(row) if row else None


def get_user_by_id(user_id):
    """Find one user by their id. Returns a dictionary, or None if not found."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


# NEW: used by the administrator to list only the Staff users.
def get_users_by_role(role):
    """Return a list of all users who have the given role (e.g. 'Staff'),
    sorted by name. The password column is NOT included on purpose."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, name, email, role, department FROM users WHERE role = ? ORDER BY name",
        (role,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ---------------------------------------------------------------
# COMPLAINTS
# ---------------------------------------------------------------
def add_complaint(student_id, title, description, category=None, location=None,
                  priority="Medium", sentiment=None):
    """Save a new complaint. Status starts as 'Pending'. Returns the new complaint id."""
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO complaints
           (student_id, title, description, category, location,
            priority, sentiment, status, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending', ?)""",
        (student_id, title, description, category,
         location, priority, sentiment, _now()),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_complaints(student_id=None, assigned_staff=None, status=None):
    """Return a list of complaints (newest first).
    With no arguments you get ALL complaints. Optional filters:
      student_id     -> only that student's complaints
      assigned_staff -> only complaints assigned to that staff member
      status         -> only complaints with that status"""
    query = "SELECT * FROM complaints"
    conditions = []
    values = []

    if student_id is not None:
        conditions.append("student_id = ?")
        values.append(student_id)
    if assigned_staff is not None:
        conditions.append("assigned_staff = ?")
        values.append(assigned_staff)
    if status is not None:
        conditions.append("status = ?")
        values.append(status)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY created_at DESC, id DESC"

    conn = get_connection()
    rows = conn.execute(query, values).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_complaint_by_id(complaint_id):
    """Return one complaint as a dictionary, or None if it does not exist."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM complaints WHERE id = ?", (complaint_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_complaint_status(complaint_id, new_status):
    """Change a complaint's status (e.g. 'Pending', 'In Progress', 'Resolved').
    When the status becomes 'Resolved' we record the time in resolved_at.
    If it moves away from 'Resolved', resolved_at is cleared.
    Returns True if a complaint was updated."""
    resolved_at = _now() if new_status == "Resolved" else None

    conn = get_connection()
    cursor = conn.execute(
        "UPDATE complaints SET status = ?, resolved_at = ? WHERE id = ?",
        (new_status, resolved_at, complaint_id),
    )
    conn.commit()
    updated = cursor.rowcount > 0  # rowcount = how many rows were changed
    conn.close()
    return updated


# NEW: assigns (or reassigns) a complaint to a staff member.
def assign_complaint(complaint_id, staff_id):
    """Save staff_id into the complaint's assigned_staff column.
    Works for a first assignment AND for reassignment (it simply overwrites).
    Returns True if the complaint was updated, or False if the staff id does
    not belong to a user with the role 'Staff' or the complaint does not exist."""

    # Safety check: only real Staff users can be assigned complaints.
    staff_member = get_user_by_id(staff_id)
    if staff_member is None or staff_member["role"] != "Staff":
        return False

    conn = get_connection()
    cursor = conn.execute(
        "UPDATE complaints SET assigned_staff = ? WHERE id = ?",
        (staff_id, complaint_id),
    )
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated


# ---------------------------------------------------------------
# RESPONSES (staff replies)
# ---------------------------------------------------------------
def add_response(complaint_id, staff_id, response):
    """Save a staff reply to a complaint. Returns the new response id."""
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO responses (complaint_id, staff_id, response, created_at) VALUES (?, ?, ?, ?)",
        (complaint_id, staff_id, response, _now()),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_responses(complaint_id):
    """Return all replies for one complaint, oldest first.
    We JOIN the users table so each reply also includes the staff member's name."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT responses.*, users.name AS staff_name
           FROM responses
           JOIN users ON users.id = responses.staff_id
           WHERE responses.complaint_id = ?
           ORDER BY responses.created_at ASC, responses.id ASC""",
        (complaint_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ---------------------------------------------------------------
# AI ANALYSIS
# ---------------------------------------------------------------
def save_ai_analysis(complaint_id, category, sentiment, priority,
                     confidence, summary, suggested_response):
    """Save the AI analysis for a complaint. Each complaint keeps ONE
    analysis, so any older one is replaced. Returns the new analysis id."""
    conn = get_connection()
    conn.execute("DELETE FROM ai_analysis WHERE complaint_id = ?",
                 (complaint_id,))
    cursor = conn.execute(
        """INSERT INTO ai_analysis
           (complaint_id, category, sentiment, priority, confidence, summary, suggested_response)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (complaint_id, category, sentiment, priority,
         confidence, summary, suggested_response),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_ai_analysis(complaint_id):
    """Return the saved AI analysis for a complaint, or None if there is none."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM ai_analysis WHERE complaint_id = ?", (complaint_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None
