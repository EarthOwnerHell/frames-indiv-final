"""Сохранение и загрузка данных приложения в формате JSON.

JSON остаётся форматом хранения, а приложение работает с объектами:
при загрузке словари превращаются в объекты Customer, Courier и Order,
при сохранении — обратно в словари. Связи заказа с клиентом и курьером
хранятся в файле в виде идентификаторов customer_id и courier_id.
"""

import json
import os
from datetime import datetime

from models import Courier, Customer, Order
from models.couriers import find_courier_by_id
from models.customers import find_customer_by_id

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CUSTOMERS_FILE = os.path.join(DATA_DIR, "customers.json")
COURIERS_FILE = os.path.join(DATA_DIR, "couriers.json")
ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")


def load_json(filename: str) -> list[dict]:
    """Загрузить список данных из JSON-файла.

    Отсутствие файла или повреждённый JSON не прерывают программу:
    в этом случае возвращается пустой список.
    """
    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print(f"Файл {filename} повреждён, данные не загружены")
        return []
    if not isinstance(data, list):
        print(f"Файл {filename} имеет неверный формат, данные не загружены")
        return []
    return data


def save_json(filename: str, data: list[dict]) -> None:
    """Сохранить список данных в JSON-файл.

    Каталог для файла создаётся автоматически, если ещё не существует.
    """
    directory = os.path.dirname(filename)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
        file.write("\n")


def load_customers(filename: str) -> list[Customer]:
    """Загрузить клиентов из JSON-файла и создать объекты Customer."""
    customers = []
    for data in load_json(filename):
        try:
            customers.append(Customer.from_data(data))
        except (KeyError, TypeError):
            print(f"Пропущена некорректная запись клиента: {data}")
    return customers


def save_customers(filename: str, customers: list[Customer]) -> None:
    """Сохранить объекты Customer в JSON-файл."""
    save_json(filename, [
        {"id": customer.id, "name": customer.name, "phone": customer.phone}
        for customer in customers
    ])


def load_couriers(filename: str) -> list[Courier]:
    """Загрузить курьеров из JSON-файла и создать объекты Courier."""
    couriers = []
    for data in load_json(filename):
        try:
            couriers.append(Courier.from_data(data))
        except (KeyError, TypeError):
            print(f"Пропущена некорректная запись курьера: {data}")
    return couriers


def save_couriers(filename: str, couriers: list[Courier]) -> None:
    """Сохранить объекты Courier в JSON-файл."""
    save_json(filename, [
        {
            "id": courier.id,
            "name": courier.name,
            "type": courier.type,
            "is_free": courier.is_free,
        }
        for courier in couriers
    ])


def order_from_data(
    data: dict, customers: list[Customer], couriers: list[Courier]
) -> Order:
    """Создать объект Order из словаря, восстановив связи с объектами.

    Вызывает LookupError, если клиент или курьер с указанным
    идентификатором не найден.
    """
    customer = find_customer_by_id(customers, data["customer_id"])
    if customer is None:
        raise LookupError(f"клиент id={data['customer_id']} не найден")
    courier = None
    if data["courier_id"] is not None:
        courier = find_courier_by_id(couriers, data["courier_id"])
        if courier is None:
            raise LookupError(f"курьер id={data['courier_id']} не найден")
    order = Order(
        order_id=data["id"],
        customer=customer,
        distance_km=data["distance_km"],
        weight=data["weight"],
        goods_sum=data["goods_sum"],
        payment_is_online=data["payment_is_online"],
        created_at=datetime.fromisoformat(data["created_at"]),
        courier=courier,
    )
    order.is_cancelled = data["is_cancelled"]
    return order


def load_orders(
    filename: str, customers: list[Customer], couriers: list[Courier]
) -> list[Order]:
    """Загрузить заказы из JSON-файла и создать объекты Order.

    Записи с несуществующим клиентом или курьером, а также записи
    с некорректными данными пропускаются с предупреждением.
    """
    orders = []
    for data in load_json(filename):
        try:
            orders.append(order_from_data(data, customers, couriers))
        except LookupError as error:
            print(f"Пропущен заказ {data.get('id')}: {error}")
        except (TypeError, ValueError) as error:
            print(f"Пропущен некорректный заказ {data.get('id')}: {error}")
    return orders


def save_orders(filename: str, orders: list[Order]) -> None:
    """Сохранить объекты Order в JSON-файл.

    Ссылки на объекты клиента и курьера заменяются их идентификаторами.
    """
    save_json(filename, [
        {
            "id": order.id,
            "customer_id": order.customer.id,
            "courier_id": order.courier.id if order.courier else None,
            "distance_km": order.distance_km,
            "weight": order.weight,
            "goods_sum": order.goods_sum,
            "payment_is_online": order.payment_is_online,
            "created_at": order.created_at.isoformat(),
            "is_cancelled": order.is_cancelled,
        }
        for order in orders
    ])


def load_all() -> tuple[list[Customer], list[Courier], list[Order]]:
    """Загрузить клиентов, курьеров и заказы со связями между ними."""
    customers = load_customers(CUSTOMERS_FILE)
    couriers = load_couriers(COURIERS_FILE)
    orders = load_orders(ORDERS_FILE, customers, couriers)
    return customers, couriers, orders
