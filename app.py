from flask import Flask, session, redirect, url_for, request, render_template, flash
import sqlite3
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-key")

DATABASE_NAME = "metroline.db"


# =========================
# DATABASE CONNECTION
# =========================
def get_db():
    connection = sqlite3.connect(DATABASE_NAME)
    connection.row_factory = sqlite3.Row
    return connection


# =========================
# ROUTE ORDER HELPER
# =========================
def resequence_routes():
    db = get_db()

    routes = db.execute("""
        SELECT id
        FROM routes
        ORDER BY display_order ASC, route_number ASC
    """).fetchall()

    for index, route in enumerate(routes, start=1):
        db.execute("""
            UPDATE routes
            SET display_order = ?
            WHERE id = ?
        """, (index, route["id"]))

    db.commit()
    db.close()

# =========================
# TIME HELPERS
# =========================
def calculate_time_difference(start_time, end_time):
    if not start_time or not end_time:
        return ""

    try:
        start = datetime.strptime(start_time, "%H:%M")
        end = datetime.strptime(end_time, "%H:%M")

        if end < start:
            end += timedelta(days=1)

        difference = end - start
        total_minutes = int(difference.total_seconds() // 60)

        hours = total_minutes // 60
        minutes = total_minutes % 60

        return f"{hours}h {minutes}m"

    except ValueError:
        return ""


def time_text_to_minutes(time_text):
    if not time_text:
        return 0

    time_text = time_text.lower().strip()
    total_minutes = 0

    try:
        if "h" in time_text:
            hours_part = time_text.split("h")[0].strip()
            total_minutes += int(hours_part) * 60

            minutes_part = time_text.split("h")[1].replace("m", "").strip()
            if minutes_part:
                total_minutes += int(minutes_part)

        elif "m" in time_text:
            total_minutes += int(time_text.replace("m", "").strip())

        else:
            total_minutes += int(time_text)

    except ValueError:
        return 0

    return total_minutes


def minutes_to_time_text(total_minutes):
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}h {minutes}m"


def calculate_stand_time_total(first_stand_time, second_stand_time):
    first_minutes = time_text_to_minutes(first_stand_time)
    second_minutes = time_text_to_minutes(second_stand_time)

    total_minutes = first_minutes + second_minutes
    return minutes_to_time_text(total_minutes)


def check_break_compliance(total_duty_time, accumulated_break):
    duty_minutes = time_text_to_minutes(total_duty_time)
    break_minutes = time_text_to_minutes(accumulated_break)

    if duty_minutes == 0:
        return "Not checked"

    if duty_minutes <= 330:
        return "OK - under 5h30 rule"

    if break_minutes >= 45:
        return "OK - compliant break"

    if break_minutes >= 30:
        return "Warning - partial break"

    return "Violation - insufficient break"


# =========================
# ROLE PERMISSIONS
# =========================
def supervisor_required():
    if "user_id" not in session:
        flash("Please log in first.", "error")
        return redirect(url_for("login"))

    if session.get("role") not in ["supervisor", "manager"]:
        flash("You do not have permission.", "error")
        return redirect(url_for("dashboard"))

    return None


# =========================
# LANDING PAGE
# =========================
@app.route("/")
def landing():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))

    return render_template("landing.html")


# =========================
# DASHBOARD
# =========================
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()

    total_routes = db.execute("SELECT COUNT(*) FROM routes").fetchone()[0]
    total_logs = db.execute("SELECT COUNT(*) FROM logs").fetchone()[0]

    todays_logs = db.execute("""
        SELECT COUNT(*)
        FROM logs
        WHERE DATE(created_at) = DATE('now')
    """).fetchone()[0]

    recent_logs = db.execute("""
        SELECT logs.*, users.username
        FROM logs
        JOIN users ON logs.user_id = users.id
        ORDER BY logs.created_at DESC
        LIMIT 6
    """).fetchall()

    route_activity = db.execute("""
        SELECT route_number, COUNT(*) AS log_count
        FROM logs
        GROUP BY route_number
        ORDER BY log_count DESC
        LIMIT 5
    """).fetchall()

    db.close()

    return render_template(
        "index.html",
        total_routes=total_routes,
        total_logs=total_logs,
        todays_logs=todays_logs,
        recent_logs=recent_logs,
        route_activity=route_activity
    )

# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()

        user = db.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        db.close()

        if user and password == "password123":
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            if user["role"] == "driver":
                return redirect(url_for("employee_check"))

            return redirect(url_for("dashboard"))

        flash("Invalid username or password", "error")

    return render_template("login.html")


# =========================
# EMPLOYEE CHECK
# =========================
@app.route("/employee-check", methods=["GET", "POST"])
def employee_check():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "driver":
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        employee_no = request.form.get("employee_no")

        if not employee_no:
            flash("Please enter your employee number", "error")
            return redirect(url_for("employee_check"))

        session["employee_no"] = employee_no
        return redirect(url_for("add_log"))

    return render_template("employee_check.html")


# =========================
# ADD LOG
# =========================
@app.route("/add_log", methods=["GET", "POST"])
def add_log():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("role") != "driver":
        return "Access denied", 403

    if not session.get("employee_no"):
        return redirect(url_for("employee_check"))

    if request.method == "POST":
        db = get_db()

        garage = request.form.get("garage", "W")
        log_date = request.form.get("log_date")

        route_number = request.form["route_number"]
        running_no = request.form["running_no"]
        fleet_no = request.form["fleet_no"]

        route_2 = request.form.get("route_2")
        running_no_2 = request.form.get("running_no_2")
        fleet_no_2 = request.form.get("fleet_no_2")

        route_3 = request.form.get("route_3")
        running_no_3 = request.form.get("running_no_3")
        fleet_no_3 = request.form.get("fleet_no_3")

        duty = request.form["duty"]
        employee_no = request.form["employee_no"]
        driver_name = request.form.get("driver_name")

        sign_on = request.form.get("sign_on")
        sign_off = request.form.get("sign_off")

        first_spell_takeover = request.form.get("first_spell_takeover")
        first_spell_time = request.form.get("first_spell_time")
        first_spell_stand_time = request.form.get("first_spell_stand_time")

        second_spell_takeover = request.form.get("second_spell_takeover")
        second_spell_time = request.form.get("second_spell_time")
        second_spell_stand_time = request.form.get("second_spell_stand_time")

        depart_terminal_point = request.form.get("depart_terminal_point")
        depart_terminal_time = request.form.get("depart_terminal_time")
        arrive_terminal_point = request.form.get("arrive_terminal_point")
        arrive_terminal_time = request.form.get("arrive_terminal_time")

        driving_time_total = calculate_time_difference(
            depart_terminal_time,
            arrive_terminal_time
        )

        stand_time_total = calculate_stand_time_total(
            first_spell_stand_time,
            second_spell_stand_time
        )

        manual_break = request.form.get("accumulated_break")

        if manual_break:
            accumulated_break = manual_break
        else:
            accumulated_break = stand_time_total

        total_duty_time = calculate_time_difference(sign_on, sign_off)

        break_compliance_status = check_break_compliance(
            total_duty_time,
            accumulated_break
        )

        supervisor_name = request.form.get("supervisor_name")
        supervisor_signature = request.form.get("supervisor_signature")
        supervisor_signed_at = None

        if supervisor_signature:
            supervisor_signed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        curtailment_points = request.form.get("curtailment_points")
        off_bus_point_stand_time = request.form.get("off_bus_point_stand_time")
        accumulated_stand_time_total = request.form.get("accumulated_stand_time_total")
        lost_mileage_code = request.form.get("lost_mileage_code")
        remarks = request.form.get("remarks")

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        db.execute("""
            INSERT INTO logs (
                user_id, garage, log_date,
                route_number, running_no, fleet_no,
                route_2, running_no_2, fleet_no_2,
                route_3, running_no_3, fleet_no_3,
                duty, employee_no, driver_name,
                sign_on, sign_off,
                first_spell_takeover, first_spell_time, first_spell_stand_time,
                second_spell_takeover, second_spell_time, second_spell_stand_time,
                depart_terminal_point, depart_terminal_time,
                arrive_terminal_point, arrive_terminal_time,
                driving_time_total, stand_time_total,
                accumulated_break, total_duty_time,
                break_compliance_status,
                supervisor_name, supervisor_signature, supervisor_signed_at,
                curtailment_points, off_bus_point_stand_time,
                accumulated_stand_time_total, lost_mileage_code,
                remarks, created_at
            ) VALUES (
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?,
                ?, ?, ?,
                ?, ?,
                ?, ?,
                ?, ?
            )
        """, (
            session["user_id"], garage, log_date,
            route_number, running_no, fleet_no,
            route_2, running_no_2, fleet_no_2,
            route_3, running_no_3, fleet_no_3,
            duty, employee_no, driver_name,
            sign_on, sign_off,
            first_spell_takeover, first_spell_time, first_spell_stand_time,
            second_spell_takeover, second_spell_time, second_spell_stand_time,
            depart_terminal_point, depart_terminal_time,
            arrive_terminal_point, arrive_terminal_time,
            driving_time_total, stand_time_total,
            accumulated_break, total_duty_time,
            break_compliance_status,
            supervisor_name, supervisor_signature, supervisor_signed_at,
            curtailment_points, off_bus_point_stand_time,
            accumulated_stand_time_total, lost_mileage_code,
            remarks, created_at
        ))

        db.commit()
        db.close()

        session["employee_no"] = employee_no

        flash("Driver log saved successfully", "success")
        return redirect(url_for("add_log"))

    return render_template("add_log.html")


# =========================
# VIEW LOGS
# =========================
@app.route("/logs")
def logs_page():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()

    logs = db.execute("""
        SELECT logs.*, users.username
        FROM logs
        JOIN users ON logs.user_id = users.id
        ORDER BY logs.created_at DESC
    """).fetchall()

    db.close()

    return render_template("logs.html", logs=logs)


# =========================
# ROUTES PAGE
# =========================
@app.route("/routes")
def routes_page():
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()

    routes = db.execute("""
        SELECT *
        FROM routes
        ORDER BY display_order ASC
    """).fetchall()

    db.close()

    return render_template("routes.html", routes=routes)

# =========================
# ADD ROUTE (SUPERVISOR ONLY)
# =========================
@app.route("/add-route", methods=["GET", "POST"])
def add_route():
    permission_check = supervisor_required()
    if permission_check:
        return permission_check

    if request.method == "POST":
        route_number = request.form.get("route_number")
        start_point = request.form.get("start_point")
        end_point = request.form.get("end_point")
        notes = request.form.get("notes")

        db = get_db()

        next_order = db.execute("""
            SELECT COALESCE(MAX(display_order), 0) + 1
            FROM routes
        """).fetchone()[0]

        db.execute("""
            INSERT INTO routes (
                route_number,
                start_point,
                end_point,
                notes,
                display_order
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            route_number,
            start_point,
            end_point,
            notes,
            next_order
        ))

        db.commit()
        db.close()

        flash("Route added successfully.", "success")
        return redirect(url_for("routes_page"))

    return render_template("add_route.html")

# =========================
# DELETE ROUTE (SUPERVISOR ONLY)
# =========================
@app.route("/delete_route/<route_number>", methods=["POST"])
def delete_route(route_number):
    permission_check = supervisor_required()
    if permission_check:
        return permission_check

    db = get_db()

    db.execute("""
        DELETE FROM routes
        WHERE route_number = ?
    """, (route_number,))

    db.commit()
    db.close()

    resequence_routes()

    flash("Route removed successfully", "success")
    return redirect(url_for("routes_page"))

# =========================
# ROUTE DETAIL PAGE
# =========================
@app.route("/route/<route_number>")
def route_detail(route_number):
    if "user_id" not in session:
        return redirect(url_for("login"))

    db = get_db()

    route = db.execute("""
        SELECT *
        FROM routes
        WHERE route_number = ?
    """, (route_number,)).fetchone()

    db.close()

    if route is None:
        return "Route not found", 404

    return render_template("route_detail.html", route=route)


# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)