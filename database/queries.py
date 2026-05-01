import datetime
from database.db import get_db


def _date_clause(date_from, date_to):
    parts, params = [], []
    if date_from:
        parts.append("AND date >= ?")
        params.append(date_from)
    if date_to:
        parts.append("AND date <= ?")
        params.append(date_to)
    return (" " + " ".join(parts) if parts else "", params)


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


def get_summary_stats(user_id, date_from=None, date_to=None):
    conn = get_db()

    date_sql, date_params = _date_clause(date_from, date_to)

    row_a = conn.execute(
        "SELECT COALESCE(SUM(amount), 0.0) AS total_spent, COUNT(*) AS transaction_count "
        "FROM expenses WHERE user_id = ?" + date_sql,
        (user_id, *date_params),
    ).fetchone()

    row_b = conn.execute(
        "SELECT category FROM expenses WHERE user_id = ?" + date_sql + " "
        "GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
        (user_id, *date_params),
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


def get_recent_transactions(user_id, limit=10, date_from=None, date_to=None):
    conn = get_db()

    date_sql, date_params = _date_clause(date_from, date_to)

    rows = conn.execute(
        "SELECT date, description, category, amount "
        "FROM expenses WHERE user_id = ?" + date_sql + " "
        "ORDER BY date DESC, id DESC "
        "LIMIT ?",
        (user_id, *date_params, limit),
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


def get_category_breakdown(user_id, date_from=None, date_to=None):
    conn = get_db()

    date_sql, date_params = _date_clause(date_from, date_to)

    rows = conn.execute(
        "SELECT category, SUM(amount) AS total "
        "FROM expenses WHERE user_id = ?" + date_sql + " "
        "GROUP BY category ORDER BY total DESC",
        (user_id, *date_params),
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
