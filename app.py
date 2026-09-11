import sqlite3
from datetime import date
from pathlib import Path

from flask import Flask, g, jsonify, render_template, request

DB_PATH = Path(__file__).parent / "expenses.db"
CATEGORIES = [
    "Food",
    "Transport",
    "Housing",
    "Utilities",
    "Entertainment",
    "Health",
    "Shopping",
    "Other",
]

app = Flask(__name__)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    with sqlite3.connect(DB_PATH) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                amount REAL NOT NULL
            )
            """
        )


@app.route("/")
def index():
    return render_template("index.html", categories=CATEGORIES)


@app.route("/api/expenses", methods=["GET"])
def list_expenses():
    category = request.args.get("category")
    month = request.args.get("month")  # format: YYYY-MM

    query = "SELECT * FROM expenses WHERE 1=1"
    params = []
    if category:
        query += " AND category = ?"
        params.append(category)
    if month:
        query += " AND date LIKE ?"
        params.append(f"{month}%")
    query += " ORDER BY date DESC, id DESC"

    rows = get_db().execute(query, params).fetchall()
    expenses = [dict(row) for row in rows]
    total = sum(e["amount"] for e in expenses)

    by_category = {}
    for e in expenses:
        by_category[e["category"]] = by_category.get(e["category"], 0) + e["amount"]

    return jsonify(
        {
            "expenses": expenses,
            "total": round(total, 2),
            "by_category": {k: round(v, 2) for k, v in by_category.items()},
        }
    )


@app.route("/api/expenses", methods=["POST"])
def add_expense():
    data = request.get_json(force=True) or {}

    expense_date = (data.get("date") or "").strip() or date.today().isoformat()
    category = (data.get("category") or "").strip()
    description = (data.get("description") or "").strip()
    amount = data.get("amount")

    if category not in CATEGORIES:
        return jsonify({"error": "Invalid category"}), 400
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return jsonify({"error": "Amount must be a number"}), 400
    if amount <= 0:
        return jsonify({"error": "Amount must be greater than 0"}), 400

    db = get_db()
    cur = db.execute(
        "INSERT INTO expenses (date, category, description, amount) VALUES (?, ?, ?, ?)",
        (expense_date, category, description, amount),
    )
    db.commit()

    row = db.execute("SELECT * FROM expenses WHERE id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201


@app.route("/api/expenses/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    db = get_db()
    db.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    db.commit()
    return "", 204


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
