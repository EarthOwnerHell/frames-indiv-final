import os
import sqlite3

import pytest

import storage
from db import database, import_json


@pytest.fixture
def db(tmp_path, monkeypatch):
    """Временная база, заполненная из рабочих JSON-файлов проекта."""
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "test.sqlite"))
    import_json.main()
    conn = database.get_connection()
    yield conn
    conn.close()


def test_schema_creates_tables(db):
    tables = {
        row["name"] for row in db.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    assert tables == {"customers", "couriers", "orders"}


def test_orders_have_foreign_keys(db):
    references = {
        row["table"] for row in db.execute("PRAGMA foreign_key_list(orders)")
    }
    assert references == {"customers", "couriers"}


def test_import_copies_all_json_records(db):
    for table, filename in (
        ("customers", storage.CUSTOMERS_FILE),
        ("couriers", storage.COURIERS_FILE),
        ("orders", storage.ORDERS_FILE),
    ):
        count = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        assert count == len(storage.load_json(filename))


def test_import_can_be_repeated(db):
    import_json.main()
    count = db.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    assert count == len(storage.load_json(storage.ORDERS_FILE))


def test_foreign_keys_are_enforced(db):
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO orders (id, customer_id, courier_id, distance_km, "
            "weight, goods_sum, payment_is_online, created_at) "
            "VALUES (1, 999, NULL, 1, 1, 1, 1, '2026-01-01T10:00:00')"
        )


def test_missing_database_gives_clear_error(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "none.sqlite"))
    with pytest.raises(FileNotFoundError, match="db.import_json"):
        database.get_connection()
    assert not os.path.exists(database.DB_PATH)


def test_all_queries_from_file_run(db):
    path = os.path.join(database.BASE_DIR, "sql", "queries.sql")
    with open(path, encoding="utf-8") as file:
        text = file.read()
    statements = [
        statement for statement in text.split(";")
        if "SELECT" in statement
    ]
    assert len(statements) >= 10
    for statement in statements:
        db.execute(statement).fetchall()
