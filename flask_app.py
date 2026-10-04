from flask import Flask, render_template, request, redirect, url_for, session

from utils.database import (
    get_user_by_email,
    get_user_by_id,
    add_complaint,
    save_ai_analysis,
    get_complaints,
    get_complaint_by_id,
    get_ai_analysis,
    get_responses,
    update_complaint_status,
    add_response,
    get_users_by_role,
    assign_complaint
)
from utils.ai_engine import analyze_complaint


app = Flask(__name__)

# Secret key used by Flask sessions
app.secret_key = "ai-complaint-management-secret-key"


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # Find user from the existing database
        user = get_user_by_email(email)

        # Check whether user exists and password is correct
        if user and user["password"] == password:

            # Store login information in the session
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["email"] = user["email"]
            session["role"] = user["role"]

            # Redirect according to user role
            if user["role"] == "Student":
                return redirect(url_for("student_dashboard"))

            elif user["role"] == "Staff":
                return redirect(url_for("staff_dashboard"))

            elif user["role"] == "Administrator":
                return redirect(url_for("admin_dashboard"))

            else:
                return "Invalid user role."

        return render_template(
            "login.html",
            error="Invalid email or password."
        )

    return render_template("login.html")


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


@app.route("/student/submit-complaint", methods=["GET", "POST"])
def submit_complaint():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Student":
        return redirect(url_for("login"))

    if request.method == "POST":

        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "").strip()
        location = request.form.get("location", "").strip()
        priority = request.form.get("priority", "Medium")

        # Validate required fields
        if not title or not description:
            return render_template(
                "submit_complaint.html",
                error="Title and description are required."
            )

        # Analyze the complaint using the existing AI engine
        ai_result = analyze_complaint(description)

        # Use AI category when the student does not select one
        final_category = category or ai_result["category"]

        # Save complaint to the existing database
        complaint_id = add_complaint(
            student_id=session["user_id"],
            title=title,
            description=description,
            category=final_category,
            location=location or None,
            priority=priority,
            sentiment=ai_result["sentiment"]
        )

        # Save AI analysis to the existing database
        save_ai_analysis(
            complaint_id,
            ai_result["category"],
            ai_result["sentiment"],
            ai_result["priority"],
            ai_result["confidence"],
            ai_result["summary"],
            ai_result["suggested_response"]
        )

        return redirect(url_for("student_dashboard"))

    return render_template("submit_complaint.html")


@app.route("/student/complaints")
def my_complaints():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Student":
        return redirect(url_for("login"))

    complaints = get_complaints(
        student_id=session["user_id"]
    )

    return render_template(
        "my_complaints.html",
        complaints=complaints
    )


@app.route("/student/complaint/<int:complaint_id>")
def complaint_details(complaint_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Student":
        return redirect(url_for("login"))

    complaint = get_complaint_by_id(complaint_id)

    if not complaint:
        return "Complaint not found", 404

    # Students can only view their own complaints
    if complaint["student_id"] != session["user_id"]:
        return "Access denied", 403

    ai_analysis = get_ai_analysis(complaint_id)
    responses = get_responses(complaint_id)

    return render_template(
        "complaint_details.html",
        complaint=complaint,
        ai_analysis=ai_analysis,
        responses=responses
    )


@app.route("/student")
def student_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user = {
        "id": session["user_id"],
        "name": session["name"],
        "email": session["email"],
        "role": session["role"]
    }

    return render_template(
        "student_dashboard.html",
        user=user
    )


@app.route("/staff")
def staff_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Staff":
        return redirect(url_for("login"))

    complaints = get_complaints(
        assigned_staff=session["user_id"]
    )

    return render_template(
        "staff_dashboard.html",
        complaints=complaints
    )


@app.route("/staff/complaint/<int:complaint_id>")
def staff_complaint_details(complaint_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Staff":
        return redirect(url_for("login"))

    complaint = get_complaint_by_id(complaint_id)

    if not complaint:
        return "Complaint not found", 404

    if complaint["assigned_staff"] != session["user_id"]:
        return "Access denied", 403

    ai_analysis = get_ai_analysis(complaint_id)
    responses = get_responses(complaint_id)
    staff_users = get_users_by_role("Staff")

    return render_template(
        "staff_complaint_details.html",
        complaint=complaint,
        ai_analysis=ai_analysis,
        responses=responses
    )


@app.route("/staff/complaint/<int:complaint_id>/update", methods=["POST"])
def update_staff_complaint(complaint_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Staff":
        return redirect(url_for("login"))

    complaint = get_complaint_by_id(complaint_id)

    if not complaint:
        return "Complaint not found", 404

    if complaint["assigned_staff"] != session["user_id"]:
        return "Access denied", 403

    status = request.form.get("status", "Pending")
    response_text = request.form.get("response", "").strip()

    allowed_statuses = [
        "Pending",
        "In Progress",
        "Resolved"
    ]

    if status not in allowed_statuses:
        return "Invalid status", 400

    update_complaint_status(
        complaint_id,
        status
    )

    if response_text:
        add_response(
            complaint_id,
            session["user_id"],
            response_text
        )

    return redirect(
        url_for(
            "staff_complaint_details",
            complaint_id=complaint_id
        )
    )


@app.route("/admin")
def admin_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Administrator":
        return redirect(url_for("login"))

    complaints = get_complaints()

    total_complaints = len(complaints)

    pending = sum(
        1 for complaint in complaints
        if complaint["status"] == "Pending"
    )

    in_progress = sum(
        1 for complaint in complaints
        if complaint["status"] == "In Progress"
    )

    resolved = sum(
        1 for complaint in complaints
        if complaint["status"] == "Resolved"
    )

    return render_template(
        "admin_dashboard.html",
        complaints=complaints,
        total_complaints=total_complaints,
        pending=pending,
        in_progress=in_progress,
        resolved=resolved
    )


@app.route("/admin/complaint/<int:complaint_id>")
def admin_complaint_details(complaint_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Administrator":
        return redirect(url_for("login"))

    complaint = get_complaint_by_id(complaint_id)

    if not complaint:
        return "Complaint not found", 404

    ai_analysis = get_ai_analysis(complaint_id)
    responses = get_responses(complaint_id)
    staff_users = get_users_by_role("Staff")

    return render_template(
        "admin_complaint_details.html",
        complaint=complaint,
        ai_analysis=ai_analysis,
        responses=responses,
        staff_users=staff_users
    )


@app.route("/admin/complaint/<int:complaint_id>/assign", methods=["POST"])
def assign_complaint_to_staff(complaint_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "Administrator":
        return redirect(url_for("login"))

    staff_id = request.form.get("staff_id")

    if not staff_id:
        return redirect(
            url_for(
                "admin_complaint_details",
                complaint_id=complaint_id
            )
        )

    assign_complaint(
        complaint_id,
        int(staff_id)
    )

    return redirect(
        url_for(
            "admin_complaint_details",
            complaint_id=complaint_id
        )
    )


if __name__ == "__main__":
    app.run(debug=True)
