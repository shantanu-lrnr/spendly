import datetime
import os
import sqlite3

from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash
from database.db import get_db, init_db, seed_db, create_user, get_user_by_email
from database.queries import (
    get_user_by_id, get_summary_stats,
    get_recent_transactions, get_category_breakdown,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

with app.app_context():
    init_db()
    seed_db()


def _parse_iso_date(value):
    if not value:
        return None
    try:
        datetime.date.fromisoformat(value)
        return value
    except ValueError:
        return None


def _format_label(value):
    if not value:
        return None
    try:
        return datetime.date.fromisoformat(value).strftime("%d %b %Y")
    except ValueError:
        return None


def _months_ago_start(today, n):
    month = today.month - n
    year = today.year
    while month <= 0:
        month += 12
        year -= 1
    return datetime.date(year, month, 1).isoformat()


def _build_presets(today):
    return {
        "this_month":    (today.replace(day=1).isoformat(), today.isoformat()),
        "last_3_months": (_months_ago_start(today, 3), today.isoformat()),
        "last_6_months": (_months_ago_start(today, 6), today.isoformat()),
    }


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

    user_id = session["user_id"]

    date_from = _parse_iso_date(request.args.get("date_from"))
    date_to   = _parse_iso_date(request.args.get("date_to"))

    user         = get_user_by_id(user_id)
    stats        = get_summary_stats(user_id, date_from=date_from, date_to=date_to)
    transactions = get_recent_transactions(user_id, date_from=date_from, date_to=date_to)
    categories   = get_category_breakdown(user_id, date_from=date_from, date_to=date_to)

    presets = _build_presets(datetime.date.today())

    active_preset = None
    if date_from is None and date_to is None:
        active_preset = "all_time"
    else:
        for name, (p_from, p_to) in presets.items():
            if date_from == p_from and date_to == p_to:
                active_preset = name
                break

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
        date_from=date_from,
        date_to=date_to,
        active_preset=active_preset,
        presets=presets,
        filter_label_from=_format_label(date_from),
        filter_label_to=_format_label(date_to),
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
    app.run(debug=os.environ.get("FLASK_DEBUG", "0") == "1", port=5001)
