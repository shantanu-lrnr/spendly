# Spec: Edit Expense

## Overview
This feature replaces the stub `GET /expenses/<id>/edit` route with a fully functional edit-expense flow. Logged-in users can update any of their own expenses (amount, category, date, description) via a pre-populated form. The change is persisted to the `expenses` table and the user is redirected back to their profile. This is the first update operation in the Spendly roadmap, completing the CRU portion of CRUD for expenses.

## Depends on
- Step 01 — Database Setup (expenses table exists)
- Step 03 — Login and Logout (session-based auth)
- Step 04 — Profile Page (destination after successful edit)
- Step 07 — Add Expense (establishes the add form pattern this feature mirrors)

## Routes
- `GET /expenses/<int:id>/edit` — render the edit-expense form pre-populated with existing values — logged-in only
- `POST /expenses/<int:id>/edit` — validate and update the expense, redirect to profile — logged-in only

## Database changes
No database changes. The existing `expenses` table has all required columns.

## Templates
- **Create:** `templates/edit_expense.html` — form with pre-populated fields: amount, category, date, description
- **Modify:** `templates/profile.html` — add an Edit link/button on each transaction row pointing to `url_for("edit_expense", id=expense.id)`

## Files to change
- `app.py` — replace the stub `edit_expense` route with GET+POST implementation; import `update_expense` from `database.db`
- `database/db.py` — add `update_expense(expense_id, user_id, amount, category, date, description)` helper
- `templates/profile.html` — add Edit button on each transaction row

## Files to create
- `templates/edit_expense.html` — the edit-expense form template
- `static/css/edit_expense.css` — page-specific styles

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw sqlite3 via `get_db()`
- Parameterised queries only — never f-strings in SQL
- Passwords hashed with werkzeug (not relevant here, but no new auth changes)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Redirect unauthenticated users to `/login`
- On GET, fetch the expense row and verify `expense["user_id"] == session["user_id"]`; call `abort(403)` if not the owner; call `abort(404)` if the expense does not exist
- On POST, re-validate ownership the same way before running the UPDATE
- The `update_expense` DB helper must include `WHERE id = ? AND user_id = ?` so a user can never overwrite another user's row even if the session check is bypassed
- After a successful POST, redirect to `url_for("profile")` with a flash success message
- `amount` must be a positive number — reject zero or negative values (max ₹9,999,999.99)
- `date` must be a valid ISO date (`YYYY-MM-DD`) — use `_parse_iso_date()` already in `app.py`
- `category` must be one of the fixed set in `ALLOWED_CATEGORIES`
- `description` is optional (may be blank)
- On validation failure, re-render the form with the error message and the user's submitted values (sticky form)
- The `update_expense` DB helper belongs in `database/db.py`, not in the route function
- Reuse the `_add_expense_form` helper pattern from `add_expense` — create an equivalent `_edit_expense_form` helper in `app.py`

## Definition of done
- [ ] Visiting `/expenses/<id>/edit` while logged out redirects to `/login`
- [ ] Visiting `/expenses/<id>/edit` for a non-existent expense returns 404
- [ ] Visiting `/expenses/<id>/edit` for another user's expense returns 403
- [ ] Visiting `/expenses/<id>/edit` while logged in as the owner renders a form pre-populated with the existing amount, category, date, and description
- [ ] Submitting the form with valid data updates the row in `expenses` and redirects to `/profile`
- [ ] A success flash message is visible on the profile page after redirect
- [ ] The updated values are immediately visible in the transactions list on `/profile`
- [ ] Submitting with a missing or zero/negative amount re-renders the form with an error and preserves submitted values
- [ ] Submitting with an invalid or missing date re-renders the form with an error
- [ ] Submitting with an invalid category re-renders the form with an error
- [ ] An Edit button/link is visible on each transaction row in `profile.html` and links to the correct edit URL
