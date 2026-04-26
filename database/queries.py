import datetime
from database.db import get_db


def get_user_by_id(user_id):
    conn = get_db()
    row = conn.execute(
        "SELECT id, name, email, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    conn.close()

    if row is None:
        return None

    dt = datetime.datetime.fromisoformat(row["created_at"])
    member_since = dt.strftime("%B %Y")

    words = row["name"].split()
    if len(words) == 1:
        initials = words[0][0].upper()
    else:
        initials = words[0][0].upper() + words[-1][0].upper()

    return {
        "name": row["name"],
        "email": row["email"],
        "initials": initials,
        "member_since": member_since,
    }


def get_summary_stats(user_id):
    conn = get_db()

    row_a = conn.execute(
        "SELECT COALESCE(SUM(amount), 0.0) AS total_spent, COUNT(*) AS transaction_count "
        "FROM expenses WHERE user_id = ?",
        (user_id,),
    ).fetchone()

    row_b = conn.execute(
        "SELECT category FROM expenses WHERE user_id = ? "
        "GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
        (user_id,),
    ).fetchone()

    conn.close()

    total_spent = f"{row_a['total_spent']:.2f}"
    transaction_count = row_a["transaction_count"]
    top_category = row_b["category"] if row_b is not None else "—"

    return {
        "total_spent": total_spent,
        "transaction_count": transaction_count,
        "top_category": top_category,
    }


def get_recent_transactions(user_id, limit=10):
    conn = get_db()
    rows = conn.execute(
        "SELECT date, description, category, amount "
        "FROM expenses WHERE user_id = ? "
        "ORDER BY date DESC, id DESC "
        "LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()

    if not rows:
        return []

    return [
        {
            "date": row["date"],
            "description": row["description"],
            "category": row["category"],
            "amount": f"{row['amount']:.2f}",
        }
        for row in rows
    ]


def get_category_breakdown(user_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT category, SUM(amount) AS total "
        "FROM expenses WHERE user_id = ? "
        "GROUP BY category ORDER BY total DESC",
        (user_id,),
    ).fetchall()
    conn.close()

    if not rows:
        return []

    grand_total = sum(row["total"] for row in rows)

    result = [
        {
            "name": row["category"],
            "amount": f"{row['total']:.2f}",
            "percent": int(row["total"] / grand_total * 100),
        }
        for row in rows
    ]

    remainder = 100 - sum(item["percent"] for item in result)
    result[0]["percent"] += remainder

    return result
