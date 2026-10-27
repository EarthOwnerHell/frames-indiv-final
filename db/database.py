"""Подключение к базе данных SQLite проекта и выполнение запросов."""

import os
import sqlite3
from contextlib import closing

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "delivery.sqlite")
SCHEMA_FILE = os.path.join(BASE_DIR, "sql", "schema.sql")


def get_connection(create: bool = False) -> sqlite3.Connection:
    """Открыть соединение с базой данных.

    Строки результата возвращаются как sqlite3.Row (доступ к полям по
    имени), проверка внешних ключей включается для каждого соединения.
    Без create=True отсутствующий файл базы не создаётся молча, а
    вызывает FileNotFoundError с подсказкой.
    """
    if not create and not os.path.exists(DB_PATH):
        raise FileNotFoundError(
            f"База данных {DB_PATH} не найдена: "
            "выполните python -m db.import_json"
        )
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    """Создать таблицы по SQL-скрипту sql/schema.sql."""
    with open(SCHEMA_FILE, encoding="utf-8") as file:
        conn.executescript(file.read())


def fetch_all(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    """Выполнить SELECT-запрос и вернуть все строки результата."""
    with closing(get_connection()) as conn:
        return conn.execute(sql, params).fetchall()


def fetch_one(sql: str, params: tuple = ()) -> sqlite3.Row | None:
    """Выполнить SELECT-запрос и вернуть первую строку или None."""
    with closing(get_connection()) as conn:
        return conn.execute(sql, params).fetchone()
