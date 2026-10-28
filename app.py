from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
from pathlib import Path
from datetime import date

app = Flask(__name__)
app.secret_key = "change-this-secret-key-for-production"
DB_PATH = Path(__file__).with_name("fitverse.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workout_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workout_name TEXT NOT NULL,
                completed_on TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS nutrition_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                food_name TEXT NOT NULL,
                calories INTEGER NOT NULL,
                protein REAL NOT NULL,
                logged_on TEXT NOT NULL
            )
        """)


WORKOUTS = [
    {"name": "Push Day", "category": "Strength", "duration": "45 min", "level": "Intermediate",
     "focus": "Chest, shoulders & triceps", "exercises": [("Push-ups", "3 sets × 10–15 reps"), ("Dumbbell shoulder press", "3 × 10"), ("Incline dumbbell press", "3 × 10"), ("Triceps pushdown", "3 × 12")]},
    {"name": "Pull Day", "category": "Strength", "duration": "45 min", "level": "Intermediate",
     "focus": "Back & biceps", "exercises": [("Lat pulldown", "3 sets × 10–12 reps"), ("Seated cable row", "3 × 10"), ("Dumbbell curls", "3 × 12"), ("Face pulls", "3 × 15")]},
    {"name": "Leg Day", "category": "Strength", "duration": "50 min", "level": "Intermediate",
     "focus": "Quads, hamstrings & glutes", "exercises": [("Bodyweight squats", "3 sets × 12 reps"), ("Leg press", "3 × 10"), ("Romanian deadlift", "3 × 10"), ("Calf raises", "3 × 15")]},
    {"name": "Full Body Starter", "category": "Beginner", "duration": "30 min", "level": "Beginner",
     "focus": "Build a consistent foundation", "exercises": [("March in place", "3 min warm-up"), ("Bodyweight squats", "2 × 10"), ("Wall push-ups", "2 × 10"), ("Bird dogs", "2 × 8 per side"), ("Easy walk", "5 min cool-down")]},
    {"name": "Core & Mobility", "category": "Recovery", "duration": "20 min", "level": "All levels",
     "focus": "Core stability & flexibility", "exercises": [("Dead bugs", "3 × 10"), ("Bird dogs", "3 × 8 per side"), ("Plank", "3 × 20–30 sec"), ("Hip flexor stretch", "30 sec per side")]}
]


@app.route("/")
def index():
    today = date.today().isoformat()
    with get_db() as conn:
        completed_today = conn.execute(
            "SELECT COUNT(*) FROM workout_logs WHERE completed_on = ?", (today,)
        ).fetchone()[0]
        week_logs = conn.execute(
            "SELECT completed_on, COUNT(*) AS total FROM workout_logs "
            "WHERE completed_on >= date('now', '-6 days') GROUP BY completed_on"
        ).fetchall()
        nutrition = conn.execute(
            "SELECT COALESCE(SUM(calories),0) AS calories, "
            "COALESCE(SUM(protein),0) AS protein FROM nutrition_logs WHERE logged_on = ?",
            (today,)
        ).fetchone()
        recent_workouts = conn.execute(
            "SELECT workout_name, completed_on FROM workout_logs ORDER BY id DESC LIMIT 5"
        ).fetchall()
        recent_foods = conn.execute(
            "SELECT food_name, calories, protein FROM nutrition_logs WHERE logged_on = ? ORDER BY id DESC LIMIT 5",
            (today,)
        ).fetchall()

    weekly_counts = {row["completed_on"]: row["total"] for row in week_logs}
    from datetime import datetime, timedelta
    chart_labels = []
    chart_values = []
    for offset in range(6, -1, -1):
        day = date.today() - timedelta(days=offset)
        chart_labels.append(day.strftime("%a"))
        chart_values.append(weekly_counts.get(day.isoformat(), 0))

    return render_template(
        "index.html",
        workouts=WORKOUTS,
        completed_today=completed_today,
        calories=nutrition["calories"],
        protein=round(nutrition["protein"], 1),
        recent_workouts=recent_workouts,
        recent_foods=recent_foods,
        chart_labels=chart_labels,
        chart_values=chart_values
    )


@app.route("/workouts")
def workouts():
    return render_template("workouts.html", workouts=WORKOUTS)


@app.route("/complete-workout", methods=["POST"])
def complete_workout():
    workout_name = request.form.get("workout_name", "").strip()
    valid_names = {workout["name"] for workout in WORKOUTS}
    if workout_name not in valid_names:
        flash("Please choose a valid workout.", "error")
        return redirect(request.referrer or url_for("index"))
    with get_db() as conn:
        conn.execute(
            "INSERT INTO workout_logs (workout_name, completed_on) VALUES (?, ?)",
            (workout_name, date.today().isoformat())
        )
    flash(f"Nice work! {workout_name} marked as complete.", "success")
    return redirect(request.referrer or url_for("index"))


@app.route("/nutrition", methods=["GET", "POST"])
def nutrition():
    if request.method == "POST":
        food_name = request.form.get("food_name", "").strip()
        try:
            calories = int(request.form.get("calories", "0"))
            protein = float(request.form.get("protein", "0"))
        except ValueError:
            flash("Enter valid numbers for calories and protein.", "error")
            return redirect(url_for("nutrition"))
        if not food_name or calories < 0 or protein < 0 or calories > 10000 or protein > 500:
            flash("Please enter a food name and reasonable non-negative values.", "error")
            return redirect(url_for("nutrition"))
        with get_db() as conn:
            conn.execute(
                "INSERT INTO nutrition_logs (food_name, calories, protein, logged_on) VALUES (?, ?, ?, ?)",
                (food_name, calories, protein, date.today().isoformat())
            )
        flash("Food entry added to today's log.", "success")
        return redirect(url_for("nutrition"))

    with get_db() as conn:
        entries = conn.execute(
            "SELECT id, food_name, calories, protein FROM nutrition_logs WHERE logged_on = ? ORDER BY id DESC",
            (date.today().isoformat(),)
        ).fetchall()
        totals = conn.execute(
            "SELECT COALESCE(SUM(calories),0) AS calories, COALESCE(SUM(protein),0) AS protein "
            "FROM nutrition_logs WHERE logged_on = ?", (date.today().isoformat(),)
        ).fetchone()
    return render_template("nutrition.html", entries=entries, calories=totals["calories"], protein=round(totals["protein"], 1))


@app.route("/delete-food/<int:food_id>", methods=["POST"])
def delete_food(food_id):
    with get_db() as conn:
        conn.execute("DELETE FROM nutrition_logs WHERE id = ? AND logged_on = ?", (food_id, date.today().isoformat()))
    flash("Food entry deleted.", "success")
    return redirect(url_for("nutrition"))


@app.route("/bmi", methods=["GET", "POST"])
def bmi():
    result = None
    if request.method == "POST":
        try:
            height_cm = float(request.form.get("height_cm", "0"))
            weight_kg = float(request.form.get("weight_kg", "0"))
            if not (80 <= height_cm <= 250 and 10 <= weight_kg <= 350):
                raise ValueError
            value = weight_kg / ((height_cm / 100) ** 2)
            if value < 18.5:
                category = "Below the usual adult range"
                note = "Consider discussing your goals and nutrition with a qualified health professional."
            elif value < 25:
                category = "Within the usual adult range"
                note = "BMI is only a screening measure and does not describe overall health by itself."
            elif value < 30:
                category = "Above the usual adult range"
                note = "BMI is a screening measure; consider your full health context, not this number alone."
            else:
                category = "High BMI range"
                note = "BMI is a screening measure; a qualified health professional can help interpret it."
            result = {"value": round(value, 1), "category": category, "note": note}
        except ValueError:
            flash("Enter a height from 80–250 cm and a weight from 10–350 kg.", "error")
    return render_template("bmi.html", result=result)


@app.route("/api/weekly-progress")
def weekly_progress():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT completed_on, COUNT(*) AS total FROM workout_logs "
            "WHERE completed_on >= date('now', '-6 days') GROUP BY completed_on"
        ).fetchall()
    counts = {row["completed_on"]: row["total"] for row in rows}
    from datetime import timedelta
    labels, values = [], []
    for offset in range(6, -1, -1):
        day = date.today() - timedelta(days=offset)
        labels.append(day.strftime("%a"))
        values.append(counts.get(day.isoformat(), 0))
    return jsonify({"labels": labels, "values": values})


init_db()

if __name__ == "__main__":
    app.run(debug=True)
