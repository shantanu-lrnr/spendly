# Spec: Login and Logout

## Overview
This step wires up the `/login` route so existing users can authenticate and the `/logout` route so they can end their session. The login form collects email and password; the route verifies the credentials against the hashed password in the `users` table, then writes the user's `id` and `name` into Flask's `session`. Logout clears the session and redirects to the landing page. This step introduces session-based authentication — the foundation every future protected route (profile, expense management) depends on.

## Depends on
- Step 1 — Database setup (`get_db()`, `users` table with `email` and `password_hash` columns)
- Step 2 — Registration (a user must exist to log in against)

## Routes
- `GET /login` — renders the login form — public
- `POST /login` — validates credentials, writes session, redirects to `/profile` on success — public
- `GET /logout` — clears the session, redirects to `/` — public (no auth guard needed yet)

## Database changes
No database changes. The `users` table already has all required columns.

## Templates
- **Modify:** `templates/login.html` — add `<form method="POST" action="{{ url_for('login') }}">` with fields for `email` and `password`, a submit button, and a block to display flash error messages. Preserve all existing visual design.

## Files to change
- `app.py` — convert `GET /login` stub to `GET/POST`; implement `POST /login` logic (fetch user, verify password, write session, redirect); implement `GET /logout` (clear session, redirect); import `session` from flask
- `database/db.py` — add `get_user_by_email(email)` helper that returns the matching row or `None`
- `templates/login.html` — add the POST form and flash message block

## Files to create
No new files.

## New dependencies
No new dependencies. `werkzeug.security` is already installed.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (`?` placeholders) — never f-strings in SQL
- Verify passwords with `werkzeug.security.check_password_hash` — never compare plaintext
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- `get_user_by_email()` belongs in `database/db.py`, not inline in the route
- On bad credentials flash a single generic message ("Invalid email or password") — do not reveal which field was wrong
- On success write `session["user_id"]` and `session["user_name"]` then redirect to `url_for("profile")`
- `GET /logout` must call `session.clear()` then `redirect(url_for("landing"))`
- `app.secret_key` is already set — do not change it

## Definition of done
- [ ] `GET /login` renders the login form
- [ ] Submitting valid credentials writes `session["user_id"]` and `session["user_name"]` and redirects to `/profile`
- [ ] Submitting an unknown email shows "Invalid email or password" and does not create a session
- [ ] Submitting a wrong password shows "Invalid email or password" and does not create a session
- [ ] Submitting with any empty field shows an error and does not create a session
- [ ] `GET /logout` clears the session and redirects to `/`
- [ ] After logout, `session["user_id"]` is no longer present
- [ ] Flash messages are visible on the login page when validation fails
