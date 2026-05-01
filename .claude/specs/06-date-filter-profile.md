# Spec: Date Filter for Profile Page

## Overview
Step 6 adds a date-range filter to the profile page so users can narrow their
transaction history and summary stats to a specific period. Currently the profile
page always shows all-time data; this step introduces a simple "from / to" date
picker rendered inside the existing profile template. When the user submits the
form the same `GET /profile` route re-runs all four queries scoped to the
selected date window and re-renders the page with filtered results. No new
routes are needed — the filter is expressed as query-string parameters.

## Depends on
- Step 1: Database setup (`expenses` table with `date` column exists)
- Step 2: Registration (users exist in the database)
- Step 3: Login / Logout (`session["user_id"]` is set)
- Step 4: Profile page UI (template structure already in place)
- Step 5: Backend routes for profile page (`get_summary_stats`, `get_recent_transactions`, `get_category_breakdown` exist in `database/queries.py`)

## Routes
No new routes. The existing `GET /profile` route is extended to accept two
optional query-string parameters:
- `date_from` — ISO date string (`YYYY-MM-DD`), inclusive lower bound
- `date_to`   — ISO date string (`YYYY-MM-DD`), inclusive upper bound

When both are absent the route behaves exactly as before (all-time data).

## Database changes
No database changes. The `expenses.date` column (`TEXT`, stored as `YYYY-MM-DD`)
already supports range comparisons via SQL `BETWEEN`.

## Templates
- **Modify**: `templates/profile.html`
  - Add a date-filter form above the transactions section containing:
    - A "From" date input (`type="date"`, name `date_from`)
    - A "To" date input (`type="date"`, name `date_to`)
    - A "Filter" submit button
    - A "Clear" link that navigates to `/profile` with no query params
  - Pre-populate both inputs with the current filter values when present
  - Display the active filter range as a short label (e.g. "Showing: 01 Apr 2026 – 30 Apr 2026") when a filter is active; hide it when no filter is applied
  - All four data sections (summary stats, transaction list, category breakdown) must reflect the filtered data — no template changes are needed for their rendering logic since they consume the same Jinja variables

## Files to change
- `app.py` — read `date_from` and `date_to` from `request.args` in the `profile()` view and pass them to all four query helpers
- `database/queries.py` — add optional `date_from` / `date_to` parameters to `get_summary_stats`, `get_recent_transactions`, and `get_category_breakdown`; keep existing call signatures backward-compatible (default `None`)
- `templates/profile.html` — add the date-filter form and active-filter label

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` only via `get_db()`
- Parameterised queries only — never string-format date values into SQL; use `?` placeholders and build the WHERE clause conditionally
- Foreign keys PRAGMA must be enabled on every connection (already done in `get_db()`)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- No inline styles
- Currency must always display as ₹ — never £ or $
- If only `date_from` is supplied, filter `date >= date_from` with no upper bound
- If only `date_to` is supplied, filter `date <= date_to` with no lower bound
- If neither is supplied, return all records (existing behaviour)
- Invalid date strings (non-ISO, unparseable) must be silently ignored — treat them as if the parameter was not supplied; use a try/except around `datetime.date.fromisoformat()` to validate
- `get_user_by_id` does not need date filtering — user profile data is always shown in full

## Definition of done
- [ ] Visiting `/profile` with no query params shows all-time data unchanged (no regression)
- [ ] Submitting `date_from=2026-04-01&date_to=2026-04-15` filters the transaction list to only expenses dated 01 Apr – 15 Apr 2026 (inclusive)
- [ ] Summary stats (total spent, transaction count, top category) update to reflect only the filtered date range
- [ ] Category breakdown updates to reflect only the filtered date range
- [ ] The "From" and "To" inputs are pre-populated with the submitted values after filtering
- [ ] An active-filter label is visible when a filter is applied; it is absent when no filter is active
- [ ] The "Clear" link returns the page to its unfiltered all-time state
- [ ] Supplying only `date_from` returns all expenses on or after that date
- [ ] Supplying only `date_to` returns all expenses on or before that date
- [ ] A garbage `date_from` value (e.g. `date_from=notadate`) is silently ignored and the page renders without error
