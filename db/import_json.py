"""Перенос данных из JSON-файлов проекта в базу данных SQLite.

Запуск из корня проекта: python -m db.import_json

Скрипт создаёт таблицы (если их ещё нет), очищает их и заново
загружает клиентов, курьеров и заказы из каталога data/. Повторный
запуск безопасен: база приводится в соответствие с JSON-файлами.
"""

import sqlite3

import storage
from db.database import DB_PATH, create_schema, get_connection


def import_customers(conn: sqlite3.Connection, filename: str) -> None:
    """Перенести клиентов из JSON в таблицу customers."""
    conn.executemany(
        """
        INSERT INTO customers (id, name, phone)
        VALUES (?, ?, ?)
        """,
        [
            (customer["id"], customer["name"], customer["phone"])
            for customer in storage.load_json(filename)
        ],
    )


def import_couriers(conn: sqlite3.Connection, filename: str) -> None:
    """Перенести курьеров из JSON в таблицу couriers."""
    conn.executemany(
        """
        INSERT INTO couriers (id, name, type, is_free)
        VALUES (?, ?, ?, ?)
        """,
        [
            (
                courier["id"],
                courier["name"],
                courier["type"],
                int(courier["is_free"]),
            )
            for courier in storage.load_json(filename)
        ],
    )


def import_orders(conn: sqlite3.Connection, filename: str) -> None:
    """Перенести заказы из JSON в таблицу orders."""
    conn.executemany(
        """
        INSERT INTO orders (
            id, customer_id, courier_id, distance_km, weight,
            goods_sum, payment_is_online, created_at, is_cancelled
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                order["id"],
                order["customer_id"],
                order["courier_id"],
                order["distance_km"],
                order["weight"],
                order["goods_sum"],
                int(order["payment_is_online"]),
                order["created_at"],
                int(order["is_cancelled"]),
            )
            for order in storage.load_json(filename)
        ],
    )


def import_all(conn: sqlite3.Connection) -> None:
    """Очистить таблицы и загрузить в них все данные из JSON.

    Заказы удаляются первыми и загружаются последними: они ссылаются
    на клиентов и курьеров через внешние ключи.
    """
    conn.execute("DELETE FROM orders")
    conn.execute("DELETE FROM couriers")
    conn.execute("DELETE FROM customers")
    import_customers(conn, storage.CUSTOMERS_FILE)
    import_couriers(conn, storage.COURIERS_FILE)
    import_orders(conn, storage.ORDERS_FILE)


def main() -> None:
    """Создать схему и перенести данные в одной транзакции."""
    conn = get_connection(create=True)
    try:
        create_schema(conn)
        import_all(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    print(f"Данные перенесены в {DB_PATH}")


if __name__ == "__main__":
    main()
