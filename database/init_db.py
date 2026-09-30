# database/init_db.py
# ---------------------------------------------------------------
# Run this file once to create the database and the demo users:
#
#     python database/init_db.py
#
# (Run it from the main project folder, the one that contains app.py.)
# ---------------------------------------------------------------

from utils.database import initialize_database, get_connection, DB_PATH
import sys
from pathlib import Path

# Python needs to know where to find the "utils" folder. We add the
# project root folder to Python's search path so the import below works
# even when this file is run directly from inside the database folder.
sys.path.append(str(Path(__file__).resolve().parent.parent))


if __name__ == "__main__":
    initialize_database()

    # Show a short summary so you can see it worked.
    conn = get_connection()
    users = conn.execute(
        "SELECT id, name, email, role, department FROM users").fetchall()
    conn.close()

    print(f"Database ready: {DB_PATH}")
    print(f"Users in the database: {len(users)}")
    for user in users:
        print(
            f"  {user['id']}. {user['name']} | {user['email']} | {user['role']} | {user['department']}")
