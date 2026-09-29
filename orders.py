"""Заказы: расчёт доставки, коллекция заказов и работа с ней.

Модуль объединяет функции ценообразования, перенесённые из ПР1 без
изменений логики, и новые функции для работы с коллекцией заказов:
добавление, поиск, фильтрация, сортировка и статистика.
"""

import math
from collections.abc import Iterator
from datetime import datetime, timedelta

FREE_DELIVERY_FROM = 2000.0
WORK_START_HOUR = 8
WORK_END_HOUR = 23
PREP_MINUTES = 10
OVERWEIGHT_LIMIT_KG = 10.0
OVERWEIGHT_RATE = 20.0


# --- Ценообразование (перенесено из ПР1 без изменений) ----------------

def delivery_zone(distance_km: float) -> str:
    """Название зоны доставки по расстоянию до клиента."""
    if distance_km <= 3.0:
        return "Центр"
    if distance_km <= 8.0:
        return "Городская зона"
    return "Пригород"


def zone_base_price(distance_km: float) -> float:
    """Базовый тариф доставки для зоны, руб."""
    if distance_km <= 3.0:
        return 149.0
    if distance_km <= 8.0:
        return 249.0
    return 399.0


def zone_travel_minutes(distance_km: float) -> int:
    """Ориентировочное время в пути по зоне, мин."""
    if distance_km <= 3.0:
        return 15
    if distance_km <= 8.0:
        return 30
    return 55


def weight_surcharge(weight: float) -> float:
    """Надбавка за тяжёлый заказ сверх лимита OVERWEIGHT_LIMIT_KG."""
    if weight > OVERWEIGHT_LIMIT_KG:
        extra_kg = math.ceil(weight - OVERWEIGHT_LIMIT_KG)
        return extra_kg * OVERWEIGHT_RATE
    return 0.0


def is_free_delivery(goods_sum: float) -> bool:
    """Признак бесплатной доставки при крупном заказе."""
    return goods_sum >= FREE_DELIVERY_FROM


def delivery_cost(
    distance_km: float, weight: float, goods_sum: float
) -> float:
    """Итоговая стоимость доставки с учётом веса и бесплатного порога."""
    if is_free_delivery(goods_sum):
        return 0.0
    return zone_base_price(distance_km) + weight_surcharge(weight)


def total_to_pay(
    distance_km: float, weight: float, goods_sum: float
) -> float:
    """Общая сумма к оплате: товары + доставка."""
    return goods_sum + delivery_cost(distance_km, weight, goods_sum)


def delivery_minutes(distance_km: float) -> int:
    """Полное время доставки: сборка + путь по зоне, мин."""
    return PREP_MINUTES + zone_travel_minutes(distance_km)


def planned_delivery_at(
    created_at: datetime, distance_km: float
) -> datetime:
    """Плановое время вручения заказа."""
    return created_at + timedelta(minutes=delivery_minutes(distance_km))


def tracking_number(created_at: datetime, order_id: int) -> str:
    """Трек-номер заказа: дата + номер заказа."""
    return "DLV-" + created_at.strftime("%Y%m%d") + "-" + str(order_id)


def payment_method_name(payment_is_online: bool) -> str:
    """Человекочитаемое название способа оплаты."""
    if payment_is_online:
        return "онлайн-оплата"
    return "наличные курьеру"


# --- Коллекция заказов --------------------------------------------------

def add_order(orders: list[dict], client_name: str, client_phone: str,
              distance_km: float, weight: float, goods_sum: float,
              payment_is_online: bool, created_at: datetime) -> dict:
    """Создать новый заказ и добавить его в список orders.

    Идентификатор формируется как максимальный существующий id + 1
    (или 1, если список пуст). Возвращает созданный заказ.
    """
    next_id = max((order["id"] for order in orders), default=0) + 1
    order = {
        "id": next_id,
        "client_name": client_name,
        "client_phone": client_phone,
        "distance_km": distance_km,
        "weight": weight,
        "goods_sum": goods_sum,
        "payment_is_online": payment_is_online,
        "created_at": created_at.isoformat(),
        "courier_id": None,
        "cancelled": False,
    }
    orders.append(order)
    return order


def find_orders(orders: list[dict], query: str) -> list[dict]:
    """Найти заказы по подстроке в имени или телефоне клиента."""
    query_lower = query.lower()
    return [
        order for order in orders
        if query_lower in order["client_name"].lower()
        or query_lower in order["client_phone"].lower()
    ]


def active_orders(orders: list[dict]) -> Iterator[dict]:
    """Генератор неотменённых заказов."""
    for order in orders:
        if not order["cancelled"]:
            yield order


def filter_orders_by_zone(orders: list[dict], zone: str) -> list[dict]:
    """Отобрать заказы, попадающие в указанную зону доставки."""
    return [
        order for order in active_orders(orders)
        if delivery_zone(order["distance_km"]) == zone
    ]


def sort_orders(orders: list[dict], key: str = "distance") -> list[dict]:
    """Отсортировать заказы по выбранному ключу.

    Поддерживаемые ключи: "distance", "weight", "goods_sum".
    """
    sort_keys = {
        "distance": lambda order: order["distance_km"],
        "weight": lambda order: order["weight"],
        "goods_sum": lambda order: order["goods_sum"],
    }
    if key not in sort_keys:
        raise ValueError(f"Неизвестный ключ сортировки: {key}")
    return sorted(orders, key=sort_keys[key])


def order_statistics(orders: list[dict]) -> dict:
    """Собрать статистику по активным заказам: выручка, средний чек,
    количество заказов по зонам доставки.
    """
    active = list(active_orders(orders))
    count_by_zone: dict[str, int] = {}
    for order in active:
        zone = delivery_zone(order["distance_km"])
        count_by_zone[zone] = count_by_zone.get(zone, 0) + 1

    if not active:
        return {"count": 0, "total_revenue": 0.0, "average_check": 0.0,
                "count_by_zone": count_by_zone}

    total_revenue = sum(
        total_to_pay(o["distance_km"], o["weight"], o["goods_sum"])
        for o in active
    )
    return {
        "count": len(active),
        "total_revenue": round(total_revenue, 2),
        "average_check": round(total_revenue / len(active), 2),
        "count_by_zone": count_by_zone,
    }


def cancel_order(orders: list[dict], order_id: int) -> dict:
    """Отменить заказ по идентификатору.

    Возвращает отменённый заказ. Вызывает KeyError, если заказ
    с указанным id не найден.
    """
    for order in orders:
        if order["id"] == order_id:
            order["cancelled"] = True
            return order
    raise KeyError(f"Заказ с id={order_id} не найден")
