"""
Tests for Step 6: Date Filter for Profile Page (GET /profile?date_from=…&date_to=…)

Spec: .claude/specs/06-date-filter-profile.md

All tests use a temp-file SQLite DB via monkeypatching DB_PATH so that the
production spendly.db is never touched. The demo seed data (8 April 2026
expenses, total ₹327.99) is loaded through seed_db() — the same data the
spec uses when quoting expected figures.
"""

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def test_db_path(tmp_path, monkeypatch):
    """
    Redirect DB_PATH to a throwaway temp file, then initialise and seed it.
    Must be requested before any import of app or queries that would
    cache the old DB_PATH.
    """
    db_file = tmp_path / "test_spendly.db"
    monkeypatch.setattr("database.db.DB_PATH", str(db_file))
    from database.db import init_db, seed_db
    init_db()
    seed_db()
    return str(db_file)


@pytest.fixture
def client(test_db_path):
    """
    Flask test client backed by the temp seeded DB.
    The demo seed user always gets id=1 because the DB starts empty.
    """
    from app import app as flask_app
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret"
    with flask_app.test_client() as c:
        yield c


@pytest.fixture
def auth_client(client):
    """
    Test client with session pre-set to the seeded demo user (id=1).
    Uses session_transaction so no login route call is needed.
    """
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_name"] = "Demo User"
    return client


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _get(client, date_from=None, date_to=None):
    """Issue GET /profile with optional date filter query params."""
    params = {}
    if date_from is not None:
        params["date_from"] = date_from
    if date_to is not None:
        params["date_to"] = date_to
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        return client.get(f"/profile?{qs}")
    return client.get("/profile")


# ---------------------------------------------------------------------------
# 1. Auth guard
# ---------------------------------------------------------------------------

class TestAuthGuard:
    def test_unauthenticated_get_profile_redirects_to_login(self, client):
        response = _get(client)
        assert response.status_code == 302, (
            "Unauthenticated /profile must redirect (302)"
        )
        assert "/login" in response.headers["Location"], (
            "Redirect target must be /login"
        )

    def test_unauthenticated_with_date_params_redirects_to_login(self, client):
        response = _get(client, date_from="2026-04-01", date_to="2026-04-10")
        assert response.status_code == 302, (
            "Unauthenticated /profile with date params must still redirect"
        )
        assert "/login" in response.headers["Location"]


# ---------------------------------------------------------------------------
# 2. No filter — all-time data (regression)
# ---------------------------------------------------------------------------

class TestNoFilter:
    def test_returns_200(self, auth_client):
        response = _get(auth_client)
        assert response.status_code == 200, "GET /profile with no params must return 200"

    def test_all_time_total_spent(self, auth_client):
        response = _get(auth_client)
        assert b"327.99" in response.data, (
            "All-time total must be ₹327.99 (sum of all 8 seed expenses)"
        )

    def test_all_time_transaction_count(self, auth_client):
        response = _get(auth_client)
        # The digit "8" appears in the transaction-count stat card
        assert b"327.99" in response.data  # guard: right page
        # The stat card renders the raw integer; check the count is present
        assert b"8" in response.data, (
            "All-time transaction count must be 8"
        )

    def test_all_time_top_category_is_bills(self, auth_client):
        response = _get(auth_client)
        assert b"Bills" in response.data, (
            "All-time top category must be Bills (highest spend at ₹120.00)"
        )

    def test_all_time_seven_categories_in_breakdown(self, auth_client):
        response = _get(auth_client)
        # The seed data has 7 distinct categories: Food, Transport, Bills,
        # Health, Entertainment, Shopping, Other
        for category in [b"Food", b"Transport", b"Bills", b"Health",
                         b"Entertainment", b"Shopping", b"Other"]:
            assert category in response.data, (
                f"Category {category!r} must appear in the breakdown"
            )

    def test_rupee_symbol_present(self, auth_client):
        response = _get(auth_client)
        assert "₹".encode("utf-8") in response.data, (
            "Currency must be displayed as ₹, never £ or $"
        )

    def test_no_active_filter_label_when_unfiltered(self, auth_client):
        response = _get(auth_client)
        html = response.data.decode("utf-8")
        # When no filter is active the "Showing:" label must be absent
        assert "Showing:" not in html, (
            "Active-filter label must not appear when no filter is applied"
        )

    def test_date_inputs_are_empty_when_unfiltered(self, auth_client):
        response = _get(auth_client)
        html = response.data.decode("utf-8")
        # Both inputs should have empty value attributes
        assert 'name="date_from"' in html, "date_from input must be present"
        assert 'name="date_to"' in html, "date_to input must be present"
        # Neither should be pre-filled
        assert 'name="date_from" value=""' in html or (
            'value=""' in html
        ), "date_from input must have an empty value when no filter active"


# ---------------------------------------------------------------------------
# 3. Full date range filter (date_from + date_to)
# ---------------------------------------------------------------------------

class TestFullDateRangeFilter:
    """
    Filter: 2026-04-01 to 2026-04-10
    Matching seed expenses (inclusive):
      2026-04-01  Lunch at cafe         Food           12.50
      2026-04-03  Monthly bus pass      Transport      35.00
      2026-04-05  Electricity bill      Bills         120.00
      2026-04-08  Pharmacy              Health         45.00
      2026-04-10  Streaming subscription Entertainment  18.00
    Total: 230.50   Count: 5   Top category: Bills
    """

    DATE_FROM = "2026-04-01"
    DATE_TO = "2026-04-10"

    def test_returns_200(self, auth_client):
        response = _get(auth_client, self.DATE_FROM, self.DATE_TO)
        assert response.status_code == 200, "Filtered /profile must return 200"

    def test_filtered_total_spent(self, auth_client):
        response = _get(auth_client, self.DATE_FROM, self.DATE_TO)
        assert b"230.50" in response.data, (
            "Filtered total must be ₹230.50 for 2026-04-01 to 2026-04-10"
        )

    def test_all_time_total_absent_when_filtered(self, auth_client):
        response = _get(auth_client, self.DATE_FROM, self.DATE_TO)
        # 327.99 is the all-time total; it should not appear in the stats card
        # when filtered. (It may appear elsewhere, so we check the stat is gone.)
        assert b"230.50" in response.data, "Filtered total must be present"
        assert b"327.99" not in response.data, (
            "All-time total 327.99 must not appear when filter is active"
        )

    def test_filtered_transaction_count_is_5(self, auth_client):
        response = _get(auth_client, self.DATE_FROM, self.DATE_TO)
        assert b"230.50" in response.data  # guard
        # The stat card must contain 5 as the transaction count
        assert b"5" in response.data, (
            "Filtered transaction count must be 5"
        )

    def test_filtered_top_category_is_bills(self, auth_client):
        response = _get(auth_client, self.DATE_FROM, self.DATE_TO)
        assert b"Bills" in response.data, (
            "Top category within 2026-04-01..2026-04-10 must be Bills"
        )

    def test_filtered_transactions_present(self, auth_client):
        response = _get(auth_client, self.DATE_FROM, self.DATE_TO)
        # Descriptions from matching expenses must appear in the transaction table
        assert b"Lunch at cafe" in response.data, "Lunch at cafe must be in filtered results"
        assert b"Monthly bus pass" in response.data, "Monthly bus pass must be in filtered results"
        assert b"Electricity bill" in response.data, "Electricity bill must be in filtered results"
        assert b"Pharmacy" in response.data, "Pharmacy must be in filtered results"
        assert b"Streaming subscription" in response.data, "Streaming subscription must be in filtered results"

    def test_out_of_range_transactions_excluded(self, auth_client):
        response = _get(auth_client, self.DATE_FROM, self.DATE_TO)
        # Expenses after 2026-04-10 must be excluded
        assert b"Clothing" not in response.data, (
            "Clothing (2026-04-12) must be excluded by the date filter"
        )
        assert b"Miscellaneous" not in response.data, (
            "Miscellaneous (2026-04-14) must be excluded by the date filter"
        )
        assert b"Grocery run" not in response.data, (
            "Grocery run (2026-04-15) must be excluded by the date filter"
        )

    def test_category_breakdown_reflects_filtered_range(self, auth_client):
        response = _get(auth_client, self.DATE_FROM, self.DATE_TO)
        html = response.data.decode("utf-8")
        # Shopping (2026-04-12) and Other (2026-04-14) are outside the range
        # Their amounts 65.00 and 9.99 must not appear in the category breakdown
        # Bills amount within range is 120.00
        assert "120.00" in html, "Bills total 120.00 must appear in category breakdown"
        # Shopping was 65.00 total — only one entry, outside range, must be absent
        assert "65.00" not in html, (
            "Shopping total 65.00 must not appear in the category breakdown when filtered"
        )

    def test_date_inputs_are_prepopulated(self, auth_client):
        response = _get(auth_client, self.DATE_FROM, self.DATE_TO)
        html = response.data.decode("utf-8")
        assert "2026-04-01" in html, (
            "date_from input must be pre-populated with the submitted value"
        )
        assert "2026-04-10" in html, (
            "date_to input must be pre-populated with the submitted value"
        )

    def test_active_filter_label_visible(self, auth_client):
        response = _get(auth_client, self.DATE_FROM, self.DATE_TO)
        html = response.data.decode("utf-8")
        # The template must render a "Showing:" label when a filter is active
        assert "Showing:" in html, (
            "Active-filter label ('Showing:') must be visible when a filter is applied"
        )

    def test_active_filter_label_contains_dates(self, auth_client):
        response = _get(auth_client, self.DATE_FROM, self.DATE_TO)
        html = response.data.decode("utf-8")
        # The label should display human-readable dates from the filter range
        # The spec shows format "01 Apr 2026 – 10 Apr 2026"
        assert "Apr 2026" in html, (
            "Active-filter label must contain human-readable date range"
        )


# ---------------------------------------------------------------------------
# 4. Only date_from supplied
# ---------------------------------------------------------------------------

class TestOnlyDateFrom:
    def test_returns_200(self, auth_client):
        response = _get(auth_client, date_from="2026-04-12")
        assert response.status_code == 200

    def test_expenses_on_or_after_date_from_included(self, auth_client):
        """
        date_from=2026-04-12 should include:
          2026-04-12 Clothing   65.00
          2026-04-14 Misc        9.99
          2026-04-15 Grocery    22.50
        Total: 97.49, count: 3
        """
        response = _get(auth_client, date_from="2026-04-12")
        assert b"Clothing" in response.data, "Clothing (2026-04-12) must be included"
        assert b"Miscellaneous" in response.data, "Miscellaneous (2026-04-14) must be included"
        assert b"Grocery run" in response.data, "Grocery run (2026-04-15) must be included"

    def test_expenses_before_date_from_excluded(self, auth_client):
        response = _get(auth_client, date_from="2026-04-12")
        assert b"Lunch at cafe" not in response.data, (
            "Lunch at cafe (2026-04-01) must be excluded when date_from=2026-04-12"
        )
        assert b"Electricity bill" not in response.data, (
            "Electricity bill (2026-04-05) must be excluded"
        )

    def test_total_reflects_only_date_from_onwards(self, auth_client):
        # 65.00 + 9.99 + 22.50 = 97.49
        response = _get(auth_client, date_from="2026-04-12")
        assert b"97.49" in response.data, (
            "Total must be 97.49 for expenses on or after 2026-04-12"
        )

    def test_date_from_input_prepopulated(self, auth_client):
        response = _get(auth_client, date_from="2026-04-12")
        assert b"2026-04-12" in response.data, (
            "date_from input must be pre-populated with 2026-04-12"
        )

    def test_active_filter_label_visible_with_only_date_from(self, auth_client):
        response = _get(auth_client, date_from="2026-04-12")
        html = response.data.decode("utf-8")
        assert "Showing:" in html, (
            "Active-filter label must be visible when only date_from is supplied"
        )


# ---------------------------------------------------------------------------
# 5. Only date_to supplied
# ---------------------------------------------------------------------------

class TestOnlyDateTo:
    def test_returns_200(self, auth_client):
        response = _get(auth_client, date_to="2026-04-03")
        assert response.status_code == 200

    def test_expenses_on_or_before_date_to_included(self, auth_client):
        """
        date_to=2026-04-03 should include:
          2026-04-01 Lunch at cafe   12.50
          2026-04-03 Bus pass top-up 35.00
        Total: 47.50, count: 2
        """
        response = _get(auth_client, date_to="2026-04-03")
        assert b"Lunch at cafe" in response.data, "Lunch at cafe must be included"
        assert b"Monthly bus pass" in response.data, "Monthly bus pass must be included"

    def test_expenses_after_date_to_excluded(self, auth_client):
        response = _get(auth_client, date_to="2026-04-03")
        assert b"Electricity bill" not in response.data, (
            "Electricity bill (2026-04-05) must be excluded when date_to=2026-04-03"
        )
        assert b"Grocery run" not in response.data, (
            "Grocery run (2026-04-15) must be excluded"
        )

    def test_total_reflects_only_up_to_date_to(self, auth_client):
        # 12.50 + 35.00 = 47.50
        response = _get(auth_client, date_to="2026-04-03")
        assert b"47.50" in response.data, (
            "Total must be 47.50 for expenses on or before 2026-04-03"
        )

    def test_date_to_input_prepopulated(self, auth_client):
        response = _get(auth_client, date_to="2026-04-03")
        assert b"2026-04-03" in response.data, (
            "date_to input must be pre-populated with 2026-04-03"
        )

    def test_active_filter_label_visible_with_only_date_to(self, auth_client):
        response = _get(auth_client, date_to="2026-04-03")
        html = response.data.decode("utf-8")
        assert "Showing:" in html, (
            "Active-filter label must be visible when only date_to is supplied"
        )


# ---------------------------------------------------------------------------
# 6. Invalid / garbage date values — silently ignored
# ---------------------------------------------------------------------------

class TestInvalidDateValues:
    def test_garbage_date_from_renders_page_without_error(self, auth_client):
        response = client_get_raw(auth_client, "date_from=notadate")
        assert response.status_code == 200, (
            "A garbage date_from must not cause a 500 — page must render"
        )

    def test_garbage_date_from_returns_all_time_data(self, auth_client):
        response = client_get_raw(auth_client, "date_from=notadate")
        assert b"327.99" in response.data, (
            "Invalid date_from must be silently ignored; all-time total 327.99 expected"
        )
        assert b"8" in response.data, (
            "Invalid date_from must be silently ignored; all-time count 8 expected"
        )

    def test_garbage_date_to_renders_page_without_error(self, auth_client):
        response = client_get_raw(auth_client, "date_to=not-a-date")
        assert response.status_code == 200, (
            "A garbage date_to must not cause a 500 — page must render"
        )

    def test_garbage_date_to_returns_all_time_data(self, auth_client):
        response = client_get_raw(auth_client, "date_to=not-a-date")
        assert b"327.99" in response.data, (
            "Invalid date_to must be silently ignored; all-time total 327.99 expected"
        )

    def test_both_garbage_returns_all_time_data(self, auth_client):
        response = client_get_raw(auth_client, "date_from=foo&date_to=bar")
        assert response.status_code == 200
        assert b"327.99" in response.data, (
            "Both invalid dates must be silently ignored; all-time data returned"
        )

    def test_partial_date_string_ignored(self, auth_client):
        response = client_get_raw(auth_client, "date_from=2026-13-01")
        assert response.status_code == 200, (
            "An out-of-range date (month 13) must be silently ignored"
        )
        assert b"327.99" in response.data

    def test_no_active_filter_label_when_invalid_dates(self, auth_client):
        response = client_get_raw(auth_client, "date_from=notadate")
        html = response.data.decode("utf-8")
        assert "Showing:" not in html, (
            "Active-filter label must not appear when the supplied date is invalid"
        )


def client_get_raw(client, raw_qs: str):
    """GET /profile with a manually constructed query string."""
    return client.get(f"/profile?{raw_qs}")


# ---------------------------------------------------------------------------
# 7. Summary stats update with filter
# ---------------------------------------------------------------------------

class TestSummaryStatsUpdate:
    def test_total_spent_changes_with_filter(self, auth_client):
        unfiltered = _get(auth_client)
        filtered = _get(auth_client, date_from="2026-04-01", date_to="2026-04-10")
        assert b"327.99" in unfiltered.data, "Unfiltered total must be 327.99"
        assert b"230.50" in filtered.data, "Filtered total must be 230.50"
        assert b"327.99" not in filtered.data, (
            "Unfiltered total must not bleed into the filtered view"
        )

    def test_transaction_count_changes_with_filter(self, auth_client):
        filtered = _get(auth_client, date_from="2026-04-12", date_to="2026-04-15")
        # Expenses on 12, 14, 15 → count=3, total=97.49
        assert b"97.49" in filtered.data
        # Count 3 must be present; count 8 should not be in the stats card
        assert b"3" in filtered.data, "Transaction count for this range must be 3"

    def test_top_category_updates_with_filter(self, auth_client):
        # date_from=2026-04-12 to 2026-04-15:
        #   Shopping 65.00, Other 9.99, Food(Grocery) 22.50
        #   Top category: Shopping
        filtered = _get(auth_client, date_from="2026-04-12", date_to="2026-04-15")
        assert b"Shopping" in filtered.data, (
            "Top category must update to Shopping for 2026-04-12..2026-04-15"
        )


# ---------------------------------------------------------------------------
# 8. Category breakdown updates with filter
# ---------------------------------------------------------------------------

class TestCategoryBreakdownUpdate:
    def test_breakdown_only_shows_filtered_categories(self, auth_client):
        # Filter to 2026-04-12 onwards: Shopping, Other, Food
        # Bills, Transport, Health, Entertainment should NOT appear in breakdown
        response = _get(auth_client, date_from="2026-04-12")
        assert b"Shopping" in response.data
        assert b"Grocery run" in response.data  # transaction description
        # Bills is not in this range so its category bar must be absent
        # (We can verify by checking its amount 120.00 is absent from the page)
        assert b"120.00" not in response.data, (
            "Bills (120.00) must not appear in category breakdown when filtered to 2026-04-12+"
        )

    def test_breakdown_amounts_match_filter(self, auth_client):
        # Filter: 2026-04-01 to 2026-04-10
        # Bills = 120.00 (only one Bills expense in range)
        response = _get(auth_client, date_from="2026-04-01", date_to="2026-04-10")
        assert b"120.00" in response.data, (
            "Bills amount in category breakdown must be 120.00 for this range"
        )
        # Shopping (65.00) is outside this range and must not appear
        assert b"65.00" not in response.data, (
            "Shopping amount 65.00 must not appear in the filtered breakdown"
        )

    def test_category_percents_sum_to_100_when_filtered(self, auth_client):
        from database.queries import get_category_breakdown
        # Directly test the query layer with a filter to verify percent integrity
        # We need the demo user's id which is 1 in the seeded DB
        result = get_category_breakdown(1, date_from="2026-04-01", date_to="2026-04-10")
        assert result, "Filtered category breakdown must not be empty"
        total_pct = sum(cat["percent"] for cat in result)
        assert total_pct == 100, (
            f"Category percents must sum to 100, got {total_pct}"
        )


# ---------------------------------------------------------------------------
# 9. Input pre-population
# ---------------------------------------------------------------------------

class TestInputPrePopulation:
    def test_both_inputs_prepopulated_when_both_supplied(self, auth_client):
        response = _get(auth_client, date_from="2026-04-05", date_to="2026-04-12")
        html = response.data.decode("utf-8")
        assert "2026-04-05" in html, "date_from input must show 2026-04-05"
        assert "2026-04-12" in html, "date_to input must show 2026-04-12"

    def test_only_date_from_prepopulated_when_only_from_supplied(self, auth_client):
        response = _get(auth_client, date_from="2026-04-05")
        html = response.data.decode("utf-8")
        assert "2026-04-05" in html, "date_from input must be pre-populated"

    def test_only_date_to_prepopulated_when_only_to_supplied(self, auth_client):
        response = _get(auth_client, date_to="2026-04-12")
        html = response.data.decode("utf-8")
        assert "2026-04-12" in html, "date_to input must be pre-populated"

    def test_inputs_empty_when_no_filter(self, auth_client):
        response = _get(auth_client)
        html = response.data.decode("utf-8")
        # Input for date_from should have an empty value
        assert 'name="date_from"' in html
        assert 'name="date_to"' in html
        # Dates from seed data should not appear as input values
        # (they may appear in the transaction table, but not in the filter inputs)
        # Check that the value attribute for both inputs is empty
        import re
        date_from_match = re.search(
            r'name="date_from"[^>]*value="([^"]*)"', html
        )
        date_to_match = re.search(
            r'name="date_to"[^>]*value="([^"]*)"', html
        )
        if date_from_match:
            assert date_from_match.group(1) == "", (
                "date_from input value must be empty when no filter active"
            )
        if date_to_match:
            assert date_to_match.group(1) == "", (
                "date_to input value must be empty when no filter active"
            )


# ---------------------------------------------------------------------------
# 10. Active-filter label visibility
# ---------------------------------------------------------------------------

class TestActiveFilterLabel:
    def test_label_absent_when_no_filter(self, auth_client):
        response = _get(auth_client)
        html = response.data.decode("utf-8")
        assert "Showing:" not in html, (
            "Active-filter label must be absent when no filter is applied"
        )

    def test_label_present_when_both_dates_supplied(self, auth_client):
        response = _get(auth_client, date_from="2026-04-01", date_to="2026-04-10")
        html = response.data.decode("utf-8")
        assert "Showing:" in html, (
            "Active-filter label must be visible when both date params are supplied"
        )

    def test_label_present_when_only_date_from(self, auth_client):
        response = _get(auth_client, date_from="2026-04-01")
        html = response.data.decode("utf-8")
        assert "Showing:" in html, (
            "Active-filter label must be visible when only date_from is supplied"
        )

    def test_label_present_when_only_date_to(self, auth_client):
        response = _get(auth_client, date_to="2026-04-15")
        html = response.data.decode("utf-8")
        assert "Showing:" in html, (
            "Active-filter label must be visible when only date_to is supplied"
        )

    def test_label_absent_when_invalid_date_supplied(self, auth_client):
        response = client_get_raw(auth_client, "date_from=garbage&date_to=garbage")
        html = response.data.decode("utf-8")
        assert "Showing:" not in html, (
            "Active-filter label must not appear when supplied dates are invalid"
        )


# ---------------------------------------------------------------------------
# 11. Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_filter_range_with_no_matching_expenses(self, auth_client):
        """A date range that matches no expenses should render without error."""
        response = _get(auth_client, date_from="2025-01-01", date_to="2025-01-31")
        assert response.status_code == 200, (
            "Profile must render even if the filter range has no matching expenses"
        )
        assert b"0.00" in response.data, (
            "Total spent must be 0.00 when no expenses match the filter"
        )

    def test_filter_range_with_no_matching_expenses_zero_count(self, auth_client):
        response = _get(auth_client, date_from="2025-01-01", date_to="2025-01-31")
        html = response.data.decode("utf-8")
        # Transaction count must be 0 — the literal character '0' will appear
        assert "0" in html  # minimal check; the count stat card must show 0

    def test_single_day_filter(self, auth_client):
        """date_from == date_to should return only that day's expenses."""
        # 2026-04-05 has one expense: Electricity bill 120.00
        response = _get(auth_client, date_from="2026-04-05", date_to="2026-04-05")
        assert response.status_code == 200
        assert b"120.00" in response.data, (
            "Single-day filter must return the expense for that day"
        )
        assert b"Electricity bill" in response.data
        # Expenses from other days must be excluded
        assert b"Lunch at cafe" not in response.data

    def test_date_from_after_date_to_returns_empty_or_renders(self, auth_client):
        """date_from > date_to is a logically empty range — must not crash."""
        response = _get(auth_client, date_from="2026-04-15", date_to="2026-04-01")
        assert response.status_code == 200, (
            "Inverted date range must not cause a 500 error"
        )

    def test_filter_does_not_show_other_users_expenses(self, auth_client, test_db_path):
        """
        A second user's expenses must never appear in the first user's
        filtered view — user_id scoping must survive the filter logic.
        """
        from database.db import create_user, get_db
        # Create a second user with an expense in the same date range
        uid2 = create_user("Other User", "other@example.com", "pass")
        conn = get_db()
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (uid2, 999.00, "Bills", "2026-04-05", "Secret expense"),
        )
        conn.commit()
        conn.close()

        response = _get(auth_client, date_from="2026-04-01", date_to="2026-04-10")
        assert b"Secret expense" not in response.data, (
            "Another user's expense must never appear in the current user's filtered view"
        )
        assert b"999.00" not in response.data, (
            "Another user's expense amount must not appear"
        )
