import pytest
from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
)


# ---------------------------------------------------------------------------
# Group 1: get_user_by_id
# ---------------------------------------------------------------------------

def test_get_user_by_id_returns_correct_fields(seeded_user, test_db_path):
    result = get_user_by_id(seeded_user)
    assert result is not None
    assert result["name"] == "Test User"
    assert result["email"] == "test@example.com"
    assert result["initials"] == "TU"
    assert result["member_since"] and isinstance(result["member_since"], str)


def test_get_user_by_id_nonexistent_returns_none(test_db_path):
    result = get_user_by_id(99999)
    assert result is None


# ---------------------------------------------------------------------------
# Group 2: get_summary_stats
# ---------------------------------------------------------------------------

def test_get_summary_stats_with_expenses(seeded_user_with_expenses, test_db_path):
    result = get_summary_stats(seeded_user_with_expenses)
    assert result["total_spent"] == "207.50"
    assert result["transaction_count"] == 3
    assert result["top_category"] == "Bills"


def test_get_summary_stats_no_expenses(seeded_user, test_db_path):
    result = get_summary_stats(seeded_user)
    assert result["total_spent"] == "0.00"
    assert result["transaction_count"] == 0
    assert result["top_category"] == "—"


# ---------------------------------------------------------------------------
# Group 3: get_recent_transactions
# ---------------------------------------------------------------------------

def test_get_recent_transactions_ordered_newest_first(seeded_user_with_expenses, test_db_path):
    result = get_recent_transactions(seeded_user_with_expenses)
    assert len(result) == 3
    assert result[0]["date"] == "2026-04-15"
    assert result[-1]["date"] == "2026-04-05"
    for item in result:
        assert "date" in item
        assert "description" in item
        assert "category" in item
        assert "amount" in item


def test_get_recent_transactions_no_expenses(seeded_user, test_db_path):
    assert get_recent_transactions(seeded_user) == []


def test_get_recent_transactions_respects_limit(seeded_user_with_expenses, test_db_path):
    result = get_recent_transactions(seeded_user_with_expenses, limit=2)
    assert len(result) == 2


# ---------------------------------------------------------------------------
# Group 4: get_category_breakdown
# ---------------------------------------------------------------------------

def test_get_category_breakdown_ordered_by_amount_desc(seeded_user_with_expenses, test_db_path):
    result = get_category_breakdown(seeded_user_with_expenses)
    assert result[0]["name"] == "Bills"
    assert result[0]["amount"] == "120.00"


def test_get_category_breakdown_percents_sum_to_100(seeded_user_with_expenses, test_db_path):
    result = get_category_breakdown(seeded_user_with_expenses)
    assert sum(cat["percent"] for cat in result) == 100


def test_get_category_breakdown_percent_is_int(seeded_user_with_expenses, test_db_path):
    result = get_category_breakdown(seeded_user_with_expenses)
    assert all(isinstance(cat["percent"], int) for cat in result)


def test_get_category_breakdown_uses_percent_not_pct(seeded_user_with_expenses, test_db_path):
    result = get_category_breakdown(seeded_user_with_expenses)
    assert "percent" in result[0]
    assert "pct" not in result[0]


def test_get_category_breakdown_no_expenses(seeded_user, test_db_path):
    assert get_category_breakdown(seeded_user) == []


# ---------------------------------------------------------------------------
# Group 5: Route tests
# ---------------------------------------------------------------------------

def test_profile_unauthenticated_redirects(app_client):
    response = app_client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_profile_authenticated_returns_200(app_client):
    with app_client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_name"] = "Demo User"
    response = app_client.get("/profile")
    assert response.status_code == 200


def test_profile_shows_demo_user_name(app_client):
    with app_client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_name"] = "Demo User"
    response = app_client.get("/profile")
    assert b"Demo User" in response.data


def test_profile_shows_rupee_symbol(app_client):
    with app_client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_name"] = "Demo User"
    response = app_client.get("/profile")
    assert "₹".encode("utf-8") in response.data


def test_profile_shows_correct_total(app_client):
    with app_client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_name"] = "Demo User"
    response = app_client.get("/profile")
    assert b"327.99" in response.data


def test_profile_shows_transaction_count(app_client):
    with app_client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_name"] = "Demo User"
    response = app_client.get("/profile")
    assert b"8" in response.data


def test_profile_shows_top_category(app_client):
    with app_client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_name"] = "Demo User"
    response = app_client.get("/profile")
    assert b"Bills" in response.data
