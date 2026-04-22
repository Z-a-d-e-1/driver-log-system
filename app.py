import sqlite3

connection = sqlite3.connect("metroline.db")
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('driver', 'supervisor', 'manager'))
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS routes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_number TEXT NOT NULL UNIQUE,
    start_point TEXT NOT NULL,
    end_point TEXT NOT NULL,
    notes TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    route_number TEXT NOT NULL,
    running_no TEXT NOT NULL,
    fleet_no TEXT NOT NULL,
    duty TEXT NOT NULL,
    employee_no TEXT NOT NULL,
    sign_on TEXT NOT NULL,
    sign_off TEXT,
    first_spell_takeover TEXT,
    second_spell_takeover TEXT,
    curtailment_points TEXT,
    off_bus_point_stand_time TEXT,
    accumulated_stand_time_total TEXT,
    lost_mileage_code TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (route_number) REFERENCES routes(route_number)
)
""")

routes = [
    ("16", "Cricklewood Garage", "Victoria Station", "Busy central London route"),
    ("32", "Edgware", "Kilburn Park", "High passenger flow"),
    ("112", "Ealing", "Brent Cross", "Useful cross-London corridor"),
    ("139", "Golders Green", "Waterloo", "Central route with peak congestion"),
    ("143", "Archway", "Brent Cross", "Frequent stops"),
    ("189", "Brent Cross", "Oxford Circus", "Busy shopping corridor"),
    ("210", "Brent Cross", "Finsbury Park", "Orbital route"),
    ("266", "Brent Cross", "Hammersmith", "Heavy traffic corridor"),
    ("268", "Golders Green", "Hampstead Heath", "Local corridor"),
    ("324", "Stanmore", "Brent Cross", "Suburban to retail link"),
    ("328", "Golders Green", "Chelsea", "Long cross-city route"),
    ("H2/H3", "Golders Green", "Hampstead Garden Suburb", "Local hopper service"),
    ("N32", "Edgware", "Central London", "Night route"),
    ("632", "School Route", "Local School Service", "School bus route")
]

cursor.executemany("""
INSERT OR IGNORE INTO routes (route_number, start_point, end_point, notes)
VALUES (?, ?, ?, ?)
""", routes)

connection.commit()
connection.close()

print("Database created and routes seeded successfully.")

import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, g
)
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect("metroline.db")
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view


def role_required(*allowed_roles):
    def decorator(view):
        @wraps(view)
        def wrapped_view(*args, **kwargs):
            if session.get("role") not in allowed_roles:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for("index"))
            return view(*args, **kwargs)
        return wrapped_view
    return decorator


@app.route("/")
def index():
    db = get_db()

    total_routes = db.execute("SELECT COUNT(*) AS count FROM routes").fetchone()["count"]
    total_logs = db.execute("SELECT COUNT(*) AS count FROM logs").fetchone()["count"]

    recent_logs = db.execute("""
        SELECT logs.*, users.username, routes.route_number
        FROM logs
        LEFT JOIN users ON logs.user_id = users.id
        LEFT JOIN routes ON logs.route_id = routes.id
        ORDER BY logs.created_at DESC
        LIMIT 5
    """).fetchall()

    return render_template(
        "index.html",
        total_routes=total_routes,
        total_logs=total_logs,
        recent_logs=recent_logs
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            flash("Login successful.", "success")
            return redirect(url_for("index"))

        flash("Invalid username or password.", "danger")

    return render_template("login.html")

@app.route("/route/<int:route_id>")
@login_required
def route_detail(route_id):
    db = get_db()

    route = db.execute(
        "SELECT * FROM routes WHERE id = ?",
        (route_id,)
    ).fetchone()

    if route is None:
        return "Route not found", 404

    logs = db.execute("""
        SELECT logs.*, users.username, routes.route_number
        FROM logs
        JOIN users ON logs.user_id = users.id
        JOIN routes ON logs.route_id = routes.id
        WHERE logs.route_id = ?
        ORDER BY logs.created_at DESC
    """, (route_id,)).fetchall()

    return render_template("route_detail.html", route=route, logs=logs)

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/routes")
@login_required
def routes_page():
    db = get_db()
    routes = db.execute("SELECT * FROM routes ORDER BY route_number").fetchall()
    return render_template("routes.html", routes=routes)


@app.route("/route/<int:route_id>")
@login_required
def route_detail(route_id):
    db = get_db()

    route = db.execute(
        "SELECT * FROM routes WHERE id = ?",
        (route_id,)
    ).fetchone()

    if route is None:
        return "Route not found", 404

    logs = db.execute(
        "SELECT * FROM logs WHERE route_number = ? ORDER BY time DESC",
        (route["route_number"],)
    ).fetchall()

    return render_template("route_detail.html", route=route, logs=logs)


@app.route("/add-log", methods=["GET", "POST"])
@login_required
@role_required("driver")
def add_log():
    db = get_db()
    routes = db.execute("SELECT * FROM routes ORDER BY route_number").fetchall()

    if request.method == "POST":
        route_id = request.form["route_id"]
        running_no = request.form["running_no"].strip()
        fleet_no = request.form["fleet_no"].strip()
        duty = request.form["duty"].strip()
        employee_no = request.form["employee_no"].strip()
        sign_on = request.form["sign_on"].strip()
        sign_off = request.form["sign_off"].strip()
        first_spell_takeover = request.form.get("first_spell_takeover", "").strip()
        second_spell_takeover = request.form.get("second_spell_takeover", "").strip()
        curtailment_points = request.form.get("curtailment_points", "").strip()
        off_bus_point_stand_time = request.form.get("off_bus_point_stand_time", "").strip()
        accumulated_stand_time_total = request.form.get("accumulated_stand_time_total", "").strip()
        lost_mileage_code = request.form.get("lost_mileage_code", "").strip()

        if not route_id or not running_no or not fleet_no or not duty or not employee_no or not sign_on:
            flash("Please complete all required fields.", "danger")
            return render_template("add_log.html", routes=routes)

        db.execute("""
            INSERT INTO logs (
                user_id, route_id, running_no, fleet_no, duty, employee_no,
                sign_on, sign_off, first_spell_takeover, second_spell_takeover,
                curtailment_points, off_bus_point_stand_time,
                accumulated_stand_time_total, lost_mileage_code, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session["user_id"], route_id, running_no, fleet_no, duty, employee_no,
            sign_on, sign_off, first_spell_takeover, second_spell_takeover,
            curtailment_points, off_bus_point_stand_time,
            accumulated_stand_time_total, lost_mileage_code,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        db.commit()

        flash("Log submitted successfully.", "success")
        return redirect(url_for("logs_page"))

    return render_template("add_log.html", routes=routes)


@app.route("/route/<int:route_id>")
@login_required
def route_detail(route_id):
    db = get_db()

    route = db.execute(
        "SELECT * FROM routes WHERE id = ?",
        (route_id,)
    ).fetchone()

    if route is None:
        return "Route not found", 404

    logs = db.execute("""
        SELECT logs.*, users.username, routes.route_number
        FROM logs
        JOIN users ON logs.user_id = users.id
        JOIN routes ON logs.route_id = routes.id
        WHERE logs.route_id = ?
        ORDER BY logs.created_at DESC
    """, (route_id,)).fetchall()

    return render_template("route_detail.html", route=route, logs=logs)


@app.route("/supervisor")
@login_required
@role_required("supervisor", "manager")
def supervisor_dashboard():
    db = get_db()
    logs = db.execute("""
        SELECT logs.*, routes.route_number, users.username
        FROM logs
        JOIN routes ON logs.route_id = routes.id
        JOIN users ON logs.user_id = users.id
        ORDER BY logs.created_at DESC
        LIMIT 20
    """).fetchall()

    return render_template("supervisor_dashboard.html", logs=logs)


if __name__ == "__main__":
    app.run(debug=True)