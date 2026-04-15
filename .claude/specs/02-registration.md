# Spec: Registration

## Overview
This step wires up the `/register` route so new users can create an account. The form collects name, email, and password; the route validates the input, hashes the password, inserts the user into the `users` table, On success the user is shown with a success message and redirected to login page. This is the first user-facing write operation in Spendly and is a prerequisite for all authenticated features.

## Depends on
- Step 1 — Database setup (`get_db()`, `init_db()`, `users` table must exist)

## Routes
- `POST /register` — handles form submission, creates user, redirects to `/login` on success — public

## Database changes
No database changes. The `users` table was created in Step 1 with all required columns (`id`, `name`, `email`, `password_hash`, `created_at`).

## Templates
- **Modify:** `templates/register.html` — add a `<form method="POST" action="{{ url_for('register') }}">` with fields for `name`, `email`, `password`, `confirm_password`, a submit button, and a flash message display area
-Add a block to display a flash error message (e.g. "Email already registered","Password do not match")
-keep all existing visual design

## Files to change
- `app.py` — add `POST` method to `/register` route; import `redirect`, `url_for`, `request`, `flash`, `session` from flask; add `app.secret_key`; add `create_user()` call
- `database/db.py` — add `create_user(name, email, password)` helper
- `templates/register.html` — add the form and flash message block

## Files to create
No new files.

## New dependencies
No new dependencies. `werkzeug.security` is already installed.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (`?` placeholders) — never f-strings in SQL
- Passwords hashed with `werkzeug.security.generate_password_hash` — never store plaintext
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- `create_user()` belongs in `database/db.py`, not inline in the route
- Catch `sqlite3.IntegrityError` for duplicate email and flash a user-friendly error
- Validate that `password == confirm_password` before inserting
- Validate that `name`, `email`, and `password` are all non-empty
- Use `abort(400)` only for truly malformed requests; use `flash()` + re-render for user-fixable validation errors
- `app.secret_key` must be set for `flash()` to work — use a hard-coded dev string for now (e.g. `"dev-secret-key"`)
- On success, redirect to `/login` using `redirect(url_for('login'))`

## Definition of done
- [ ] `GET /register` renders the registration form
- [ ] Submitting the form with valid data creates a new row in `users` with a hashed password
- [ ] Submitting with a duplicate email shows an error message and does not insert
- [ ] Submitting with mismatched passwords shows an error message and does not insert
- [ ] Submitting with any empty field shows an error message and does not insert
- [ ] Successful registration redirects to `/login`
- [ ] The password stored in the DB is a hash, never the plaintext value
- [ ] Flash messages are visible on the page when validation fails
