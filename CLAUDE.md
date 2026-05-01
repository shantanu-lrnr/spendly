# CLAUDE.md

## Project overview

Spendly is a lightweight personal expense tracker built with Flask and SQLite.

---

## Architecture
```
spendly/
├── app.py              # All routes — single file, no blueprints
├── database/
│   ├── db.py           # SQLite helpers: get_db(), init_db(), seed_db(), create_user(), get_user_by_email()
│   └── queries.py      # Pure query helpers (no Flask imports): get_user_by_id(), get_summary_stats(), get_recent_transactions(), get_category_breakdown()
├── templates/
│   ├── base.html       # Shared layout — all templates must extend this
│   └── *.html          # One template per page
├── static/
│   ├── css/
│   │   ├── style.css       # Global styles
│   │   ├── landing.css     # Landing-page-only styles
│   │   └── profile.css     # Profile page styles
│   └── js/
│       └── main.js         # Vanilla JS only
├── tests/
│   └── test_*.py       # pytest test files, one per feature step
└── pyproject.toml
```

**Where things belong:**
- New routes → `app.py` only, no blueprints
- DB connection/schema/seed logic → `database/db.py` only
- Pure query helpers → `database/queries.py` only, no Flask imports
- New pages → new `.html` file extending `base.html`
- Page-specific styles → new `.css` file, not inline `<style>` tags
- Module-level helpers (`_parse_iso_date`, `_format_label`, `_build_presets`, etc.) → `app.py`, above the Routes block

---

## Code style

- Python: PEP 8, snake_case for all variables and functions
- Templates: Jinja2 with `url_for()` for every internal link — never hardcode URLs
- Route functions: one responsibility only — fetch data, render template, done
- DB queries: always use parameterized queries (`?` placeholders) — never f-strings in SQL
- Error handling: use `abort()` for HTTP errors, not bare `return "error string"`

---

## Tech constraints

- **Flask only** — no FastAPI, no Django, no other web frameworks
- **SQLite only** — no PostgreSQL, no SQLAlchemy ORM, no external DB
- **Vanilla JS only** — no React, no jQuery, no npm packages
- **No new pip packages** — work within `pyproject.toml` as-is unless explicitly told otherwise
- Python 3.10+ assumed — f-strings and `match` statements are fine

---

## Commands
```bash
# Setup
uv sync

# Run dev server (port 5001)
uv run python app.py
# Or with debug mode:
FLASK_DEBUG=1 uv run python app.py

# Run all tests
uv run pytest

# Run a specific test file
uv run pytest tests/test_foo.py -v

# Run a specific test by name
uv run pytest -k "test_name"

# Run tests with output visible
uv run pytest -s
```

---

## Implemented vs stub routes

| Route | Status |
|---|---|
| `GET /` | Implemented — renders `landing.html` |
| `GET /register` | Implemented — renders `register.html` |
| `POST /register` | Implemented — creates user, redirects to login |
| `GET /login` | Implemented — renders `login.html` |
| `POST /login` | Implemented — authenticates user, sets session |
| `GET /logout` | Implemented — clears session, redirects to landing |
| `GET /profile` | Implemented — renders `profile.html` with live DB data + date filter |
| `GET /terms` | Implemented — renders `terms.html` |
| `GET /privacy` | Implemented — renders `privacy.html` |
| `GET /expenses/add` | Stub — Step 7 |
| `GET /expenses/<id>/edit` | Stub — Step 8 |
| `GET /expenses/<id>/delete` | Stub — Step 9 |

**Do not implement a stub route unless the active task explicitly targets that step.**

## Profile page — date filter

`GET /profile` accepts optional query params `date_from` and `date_to` (ISO `YYYY-MM-DD`).  
Both are validated via `_parse_iso_date()` in `app.py` — invalid strings are silently ignored.  
Preset ranges (This Month, Last 3 Months, Last 6 Months) are computed by `_build_presets(today)` at module level.  
All three expense query helpers accept `date_from=None, date_to=None` kwargs — existing callers without those args are unaffected.

---

## Warnings and things to avoid

- **Never use raw string returns for stub routes** once a step is implemented — always render a template
- **Never hardcode URLs** in templates — always use `url_for()`
- **Never put DB logic in route functions** — connection/schema logic in `database/db.py`, queries in `database/queries.py`
- **Never install new packages** mid-feature without flagging it — keep `pyproject.toml` in sync
- **Never use JS frameworks** — the frontend is intentionally vanilla
- **Never string-format values into SQL** — always use `?` parameterized queries
- **FK enforcement is manual** — SQLite foreign keys are off by default; `get_db()` runs `PRAGMA foreign_keys = ON` on every connection (already implemented)
- **Currency is always ₹** — never £ or $
- The app runs on **port 5001**, not the Flask default 5000 — don't change this
- The venv is `.venv/`, not `venv/`