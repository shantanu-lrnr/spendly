# Spec: Add Expense

## Overview
This feature replaces the stub `GET /expenses/add` route with a fully functional add-expense flow. Users can submit a form to record a new expense (amount, category, date, description) which is immediately persisted to the `expenses` table and reflected on their profile page. This is the first write operation in the Spendly roadmap and makes the app genuinely useful for tracking spending.

## Depends on
- Step 01 — Database Setup (expenses table exists)
- Step 03 — Login and Logout (session-based auth)
- Step 04 — Profile Page (destination after successful add)

## Routes
- `GET /expenses/add` — render the add-expense form — logged-in only
- `POST /expenses/add` — validate and insert the expense, redirect to profile — logged-in only

## Database changes
No database changes. The `expenses` table already exists with all required columns:
- `id`, `user_id`, `amount`, `category`, `date`, `description`, `created_at`

## Templates
- **Create:** `templates/add_expense.html` — form with fields: amount, category, date, description
- **Modify:** none

## Files to change
- `app.py` — replace the stub `add_expense` route with GET+POST implementation; add `add_expense_to_db()` call
- `database/db.py` — add `add_expense(user_id, amount, category, date, description)` helper

## Files to create
- `templates/add_expense.html` — the add-expense form template
- `static/css/add_expense.css` — page-specific styles

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw sqlite3 via `get_db()`
- Parameterised queries only — never f-strings in SQL
- Passwords hashed with werkzeug (not relevant here, but no new auth changes)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Redirect unauthenticated users to `/login`
- After a successful POST, redirect to `url_for("profile")` with a flash success message
- `amount` must be a positive number — reject zero or negative values
- `date` must be a valid ISO date (`YYYY-MM-DD`) — use `_parse_iso_date()` already in `app.py`
- `category` must be one of the fixed set used in seed data: Food, Transport, Bills, Health, Entertainment, Shopping, Other
- `description` is optional (may be blank)
- On validation failure, re-render the form with the error message and the user's previously entered values (sticky form)
- The `add_expense` DB helper belongs in `database/db.py`, not in the route function
- The route function only: validates input, calls the helper, flashes, redirects or re-renders

## Definition of done
- [ ] Visiting `/expenses/add` while logged out redirects to `/login`
- [ ] Visiting `/expenses/add` while logged in renders a form with fields: amount, category (dropdown), date, description
- [ ] Submitting the form with all valid fields inserts a row into `expenses` and redirects to `/profile`
- [ ] A success flash message is visible on the profile page after redirect
- [ ] Submitting with a missing or zero/negative amount re-renders the form with an error and preserves other field values
- [ ] Submitting with an invalid or missing date re-renders the form with an error
- [ ] Submitting with an invalid category re-renders the form with an error
- [ ] The new expense appears in the transactions list on `/profile` immediately after adding
- [ ] The summary stats on `/profile` (total, count) reflect the newly added expense
