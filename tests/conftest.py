import pytest


@pytest.fixture
def test_db_path(tmp_path, monkeypatch):
    db_file = tmp_path / "test_spendly.db"
    monkeypatch.setattr("database.db.DB_PATH", str(db_file))
    from database.db import init_db, seed_db
    init_db()
    seed_db()
    return str(db_file)


@pytest.fixture
def seeded_user(test_db_path):
    from database.db import create_user
    return create_user("Test User", "test@example.com", "password123")


@pytest.fixture
def seeded_user_with_expenses(seeded_user):
    from database.db import get_db
    conn = get_db()
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        [
            (seeded_user, 120.00, "Bills",    "2026-04-05", "Electricity bill"),
            (seeded_user,  65.00, "Shopping", "2026-04-12", "Clothing"),
            (seeded_user,  22.50, "Food",     "2026-04-15", "Grocery run"),
        ],
    )
    conn.commit()
    conn.close()
    return seeded_user


@pytest.fixture
def app_client(test_db_path):
    # Import AFTER monkeypatch so init_db/seed_db use the test DB
    from app import app as flask_app
    flask_app.config["TESTING"] = True
    flask_app.config["SECRET_KEY"] = "test-secret"
    with flask_app.test_client() as client:
        yield client
