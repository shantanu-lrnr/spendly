import sqlite3

from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from database.db import get_db, init_db, seed_db, create_user, get_user_by_email

app = Flask(__name__)
app.secret_key = "dev-secret-key"

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name or not email or not password or not confirm_password:
            return render_template(
                "register.html",
                error="All fields are required.",
                name=name,
                email=email,
            )

        if password != confirm_password:
            return render_template(
                "register.html",
                error="Passwords do not match.",
                name=name,
                email=email,
            )

        try:
            create_user(name, email, password)
        except sqlite3.IntegrityError:
            return render_template(
                "register.html",
                error="Email already registered.",
                name=name,
                email=email,
            )

        flash("Account created. Please sign in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            return render_template(
                "login.html",
                error="All fields are required.",
                email=email,
            )

        user = get_user_by_email(email)
        if user is None or not check_password_hash(user["password_hash"], password):
            return render_template(
                "login.html",
                error="Invalid email or password.",
                email=email,
            )

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        return redirect(url_for("profile"))

    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user = {
        "name": session.get("user_name", "Demo User"),
        "email": "demo@spendly.com",
        "member_since": "April 2026",
        "initials": "DU",
    }

    stats = {
        "total_spent": "327.99",
        "transaction_count": 8,
        "top_category": "Bills",
    }

    transactions = [
        {"date": "2026-04-15", "description": "Grocery run",            "category": "Food",          "amount": "22.50"},
        {"date": "2026-04-14", "description": "Miscellaneous",          "category": "Other",         "amount":  "9.99"},
        {"date": "2026-04-12", "description": "Clothing",               "category": "Shopping",      "amount": "65.00"},
        {"date": "2026-04-10", "description": "Streaming subscription", "category": "Entertainment", "amount": "18.00"},
        {"date": "2026-04-08", "description": "Pharmacy",               "category": "Health",        "amount": "45.00"},
        {"date": "2026-04-05", "description": "Electricity bill",       "category": "Bills",         "amount": "120.00"},
        {"date": "2026-04-03", "description": "Monthly bus pass",       "category": "Transport",     "amount": "35.00"},
        {"date": "2026-04-01", "description": "Lunch at cafe",          "category": "Food",          "amount": "12.50"},
    ]

    categories = [
        {"name": "Bills",         "amount": "120.00", "percent": 37},
        {"name": "Shopping",      "amount":  "65.00", "percent": 20},
        {"name": "Health",        "amount":  "45.00", "percent": 14},
        {"name": "Transport",     "amount":  "35.00", "percent": 11},
        {"name": "Food",          "amount":  "35.00", "percent": 11},
        {"name": "Entertainment", "amount":  "18.00", "percent":  5},
        {"name": "Other",         "amount":   "9.99", "percent":  3},
    ]

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
    )


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
