"""
Expense Tracker Web Application

How to run:
    pip install flask reportlab
    python app.py

Then open:
    http://127.0.0.1:5001
"""

import os
import json
import re
import sqlite3
from datetime import date, datetime
from pathlib import Path

from flask import (
    Flask,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from database import get_connection, init_db
from reports import generate_csv, generate_pdf


app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "expense-tracker-dev-key")

BASE_DIR = Path(__file__).resolve().parent
USERS_FILE = BASE_DIR / "users.json"
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,32}$")

init_db()


@app.before_request
def require_authenticated_user():
    public_endpoints = {"login", "register", "static"}
    if request.endpoint in public_endpoints or request.endpoint is None:
        return None

    if current_user():
        return None

    if request.path.startswith("/api/"):
        return jsonify({"error": "Authentication required"}), 401

    flash("Please log in to continue.", "error")
    return redirect(url_for("login", next=safe_next_url(request.full_path)))


@app.template_filter("currency")
def currency_filter(value):
    return f"${float(value or 0):,.2f}"


@app.template_filter("month_label")
def month_label_filter(value):
    return format_month_label(value)


@app.context_processor
def inject_sidebar_context():
    month = current_month()
    summary = get_summary(month)
    return {
        "sidebar_month": month,
        "sidebar_month_label": format_month_label(month),
        "sidebar_savings": summary["savings"],
        "current_user": current_user(),
    }


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user():
        return redirect(url_for("dashboard"))

    next_url = safe_next_url(request.values.get("next"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        users = load_users()
        user = users.get(user_key(username))

        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["username"] = user["username"]
            flash("Welcome back.", "success")
            return redirect(next_url or url_for("dashboard"))

        flash("Invalid username or password.", "error")

    return render_template("login.html", next_url=next_url)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user():
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        errors = validate_account(username, password, confirm_password)

        users = load_users()
        key = user_key(username)
        if key in users:
            errors.append("That username is already taken.")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("register.html", username=username), 400

        users[key] = {
            "username": username,
            "password_hash": generate_password_hash(password),
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        save_users(users)

        session.clear()
        session["username"] = username
        flash("Account created successfully.", "success")
        return redirect(url_for("dashboard"))

    return render_template("register.html", username="")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/")
def dashboard():
    selected_month = normalize_month(request.args.get("month"))
    summary = get_summary(selected_month)
    return render_template(
        "dashboard.html",
        selected_month=selected_month,
        month_options=get_month_options(selected_month),
        summary=summary,
        recent_transactions=get_transactions(limit=5),
    )


@app.route("/add", methods=["GET", "POST"])
def add_transaction():
    if request.method == "POST":
        tx_type = request.form.get("type", "").strip().lower()
        amount_raw = request.form.get("amount", "").strip()
        category_id_raw = request.form.get("category_id", "").strip()
        description = request.form.get("description", "").strip()
        tx_date = request.form.get("date", "").strip()

        errors = validate_transaction(tx_type, amount_raw, category_id_raw, tx_date)
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template(
                "add.html",
                categories=get_categories(),
                today=current_date(),
                form=request.form,
            ), 400

        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO transactions
                    (type, amount, category_id, description, date)
                VALUES (?, ?, ?, ?, ?)
                """,
                (tx_type, float(amount_raw), int(category_id_raw), description, tx_date),
            )
            conn.commit()

        flash("Transaction added successfully.", "success")
        return redirect(url_for("dashboard", month=tx_date[:7]))

    return render_template(
        "add.html",
        categories=get_categories(),
        today=current_date(),
        form={},
    )


@app.route("/history")
def history():
    selected_month = request.args.get("month", "").strip()
    selected_type = request.args.get("type", "").strip().lower()
    selected_category = request.args.get("category_id", "").strip()

    if selected_month:
        selected_month = normalize_month(selected_month)
    if selected_type not in {"", "income", "expense"}:
        selected_type = ""
    if selected_category and not selected_category.isdigit():
        selected_category = ""

    filters = {
        "month": selected_month,
        "type": selected_type,
        "category_id": selected_category,
    }
    transactions = get_transactions(**filters)
    balance = get_balance(**filters)

    return render_template(
        "history.html",
        transactions=transactions,
        categories=get_categories(),
        month_options=get_month_options(selected_month or current_month()),
        filters=filters,
        balance=balance,
    )


@app.route("/delete/<int:transaction_id>", methods=["POST"])
def delete_transaction(transaction_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
        conn.commit()
    flash("Transaction deleted.", "success")

    next_url = request.form.get("next") or url_for("history")
    if not next_url.startswith("/") or next_url.startswith("//"):
        next_url = url_for("history")
    return redirect(next_url)


@app.route("/reports")
def reports_page():
    selected_month = normalize_month(request.args.get("month"))
    return render_template(
        "reports.html",
        selected_month=selected_month,
        month_options=get_month_options(selected_month),
        summary=get_summary(selected_month),
        category_breakdown=get_category_breakdown(selected_month),
        transactions=get_transactions(month=selected_month),
    )


@app.route("/export/csv")
def export_csv():
    selected_month = normalize_month(request.args.get("month"))
    transactions = get_transactions(month=selected_month)
    buffer = generate_csv(transactions, selected_month)
    return send_file(
        buffer,
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"expense-transactions-{selected_month}.csv",
    )


@app.route("/export/pdf")
def export_pdf():
    selected_month = normalize_month(request.args.get("month"))
    buffer = generate_pdf(
        selected_month,
        get_summary(selected_month),
        get_category_breakdown(selected_month),
        get_transactions(month=selected_month),
    )
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"expense-report-{selected_month}.pdf",
    )


@app.route("/api/summary")
def api_summary():
    selected_month = normalize_month(request.args.get("month"))
    return jsonify(get_summary(selected_month))


@app.route("/api/category-breakdown")
def api_category_breakdown():
    selected_month = normalize_month(request.args.get("month"))
    return jsonify(get_category_breakdown(selected_month))


@app.route("/api/monthly-trend")
def api_monthly_trend():
    return jsonify(get_monthly_trend())


def validate_transaction(tx_type, amount_raw, category_id_raw, tx_date):
    errors = []
    if tx_type not in {"income", "expense"}:
        errors.append("Choose income or expense.")

    try:
        amount = float(amount_raw)
        if amount <= 0:
            errors.append("Amount must be greater than zero.")
    except ValueError:
        errors.append("Enter a valid amount.")

    if not category_id_raw.isdigit() or not category_exists(int(category_id_raw)):
        errors.append("Choose a valid category.")

    try:
        datetime.strptime(tx_date, "%Y-%m-%d")
    except ValueError:
        errors.append("Choose a valid date.")

    return errors


def get_categories():
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, name FROM categories ORDER BY name"
        ).fetchall()


def category_exists(category_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM categories WHERE id = ?",
            (category_id,),
        ).fetchone()
    return row is not None


def get_summary(month):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN type = 'income' THEN amount END), 0) AS income,
                COALESCE(SUM(CASE WHEN type = 'expense' THEN amount END), 0) AS expense
            FROM transactions
            WHERE substr(date, 1, 7) = ?
            """,
            (month,),
        ).fetchone()

    income = round(float(row["income"] or 0), 2)
    expense = round(float(row["expense"] or 0), 2)
    return {
        "income": income,
        "expense": expense,
        "savings": round(income - expense, 2),
    }


def get_category_breakdown(month):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT c.name AS category, ROUND(SUM(t.amount), 2) AS total
            FROM transactions t
            JOIN categories c ON c.id = t.category_id
            WHERE t.type = 'expense'
              AND substr(t.date, 1, 7) = ?
            GROUP BY c.id, c.name
            ORDER BY total DESC
            """,
            (month,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_monthly_trend():
    months = [add_months(first_day_of_current_month(), offset) for offset in range(-5, 1)]
    trend = []
    for month_date in months:
        month = month_date.strftime("%Y-%m")
        summary = get_summary(month)
        trend.append(
            {
                "month": month,
                "income": summary["income"],
                "expense": summary["expense"],
            }
        )
    return trend


def get_transactions(month=None, type=None, category_id=None, limit=None):
    clauses = []
    params = []

    if month:
        clauses.append("substr(t.date, 1, 7) = ?")
        params.append(month)
    if type:
        clauses.append("t.type = ?")
        params.append(type)
    if category_id:
        clauses.append("t.category_id = ?")
        params.append(int(category_id))

    sql = """
        SELECT
            t.id,
            t.type,
            t.amount,
            t.description,
            t.date,
            c.name AS category
        FROM transactions t
        JOIN categories c ON c.id = t.category_id
    """
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY t.date DESC, t.id DESC"
    if limit is not None:
        sql += " LIMIT ?"
        params.append(int(limit))

    with get_connection() as conn:
        return conn.execute(sql, tuple(params)).fetchall()


def get_balance(month=None, type=None, category_id=None):
    clauses = []
    params = []
    if month:
        clauses.append("substr(date, 1, 7) = ?")
        params.append(month)
    if type:
        clauses.append("type = ?")
        params.append(type)
    if category_id:
        clauses.append("category_id = ?")
        params.append(int(category_id))

    sql = """
        SELECT
            COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE -amount END), 0)
            AS balance
        FROM transactions
    """
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)

    with get_connection() as conn:
        row = conn.execute(sql, tuple(params)).fetchone()
    return round(float(row["balance"] or 0), 2)


def get_month_options(selected_month=None):
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT substr(date, 1, 7) AS month
            FROM transactions
            ORDER BY month DESC
            """
        ).fetchall()

    months = {row["month"] for row in rows if row["month"]}
    months.add(current_month())
    if selected_month:
        months.add(selected_month)

    return [
        {"value": month, "label": format_month_label(month)}
        for month in sorted(months, reverse=True)
    ]


def normalize_month(value):
    if not value:
        return current_month()
    try:
        parsed = datetime.strptime(value, "%Y-%m")
    except ValueError:
        return current_month()
    return parsed.strftime("%Y-%m")


def format_month_label(value):
    try:
        return datetime.strptime(f"{value}-01", "%Y-%m-%d").strftime("%B %Y")
    except (TypeError, ValueError):
        return format_month_label(current_month())


def current_month():
    return date.today().strftime("%Y-%m")


def current_date():
    return date.today().isoformat()


def first_day_of_current_month():
    return date.today().replace(day=1)


def add_months(value, months):
    month = value.month + months
    year = value.year
    while month > 12:
        month -= 12
        year += 1
    while month <= 0:
        month += 12
        year -= 1
    return value.replace(year=year, month=month, day=1)


def current_user():
    username = session.get("username")
    if not username:
        return None

    users = load_users()
    user = users.get(user_key(username))
    if not user:
        session.clear()
        return None
    return user["username"]


def ensure_users_file():
    if not USERS_FILE.exists():
        save_users({})


def load_users():
    if not USERS_FILE.exists():
        return {}

    try:
        data = json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}

    if not isinstance(data, dict):
        return {}
    return data


def save_users(users):
    payload = json.dumps(users, indent=4, sort_keys=True)
    USERS_FILE.write_text(payload, encoding="utf-8")


def user_key(username):
    return username.strip().lower()


def validate_account(username, password, confirm_password):
    errors = []
    if not USERNAME_PATTERN.match(username):
        errors.append("Username must be 3-32 characters using letters, numbers, or underscores.")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if password != confirm_password:
        errors.append("Passwords do not match.")
    return errors


def safe_next_url(value):
    if not value:
        return ""
    if not value.startswith("/") or value.startswith("//"):
        return ""
    return value


ensure_users_file()


@app.errorhandler(sqlite3.Error)
def handle_database_error(error):
    app.logger.exception("Database error: %s", error)
    flash("A database error occurred. Please try again.", "error")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5001"))
    app.run(host="127.0.0.1", port=port, debug=True)
