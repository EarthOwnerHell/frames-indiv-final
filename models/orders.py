"""Заказы: тарифы доставки, класс Order и функции работы с коллекцией.

Тарифные функции перенесены из ПР1 без изменений логики: это правила
сервиса, а не поведение конкретного заказа, поэтому они остаются
обычными функциями, а методы Order их используют.
"""

import math
from collections.abc import Iterator
from datetime import datetime, timedelta

from .couriers import (
    Courier,
    find_available_courier,
    is_working_time,
    order_status,
)
from .customers import Customer

FREE_DELIVERY_FROM = 2000.0
PREP_MINUTES = 10
OVERWEIGHT_LIMIT_KG = 10.0
OVERWEIGHT_RATE = 20.0


# --- Тарифы (перенесено из ПР1 без изменений) --------------------------

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


def payment_method_name(payment_is_online: bool) -> str:
    """Человекочитаемое название способа оплаты."""
    if payment_is_online:
        return "онлайн-оплата"
    return "наличные курьеру"


# --- Класс Order ------------------------------------------------------

class Order:
    """Заказ клиента на доставку.

    Заказ связывает объект Customer (кто заказал) и объект Courier
    (кто везёт; None, пока курьер не назначен).
    """

    def __init__(
        self,
        order_id: int,
        customer: Customer,
        distance_km: float,
        weight: float,
        goods_sum: float,
        payment_is_online: bool,
        created_at: datetime,
        courier: Courier | None = None,
    ) -> None:
        """Создать объект заказа.

        Вызывает ValueError, если расстояние, вес или сумма отрицательны.
        """
        for value in (distance_km, weight, goods_sum):
            if not Order.validate_amount(value):
                raise ValueError(
                    "Расстояние, вес и сумма не могут быть отрицательными"
                )
        self.id = order_id
        self.customer = customer
        self.distance_km = distance_km
        self.weight = weight
        self.goods_sum = goods_sum
        self.payment_is_online = payment_is_online
        self.created_at = created_at
        self.courier = courier
        self.is_cancelled = False

    @staticmethod
    def validate_amount(value: float) -> bool:
        """Проверить, что числовой параметр заказа неотрицателен."""
        return value >= 0

    @property
    def zone(self) -> str:
        """Зона доставки заказа."""
        return delivery_zone(self.distance_km)

    @property
    def status(self) -> str:
        """Текущее состояние заказа."""
        if self.is_cancelled:
            return "отменён"
        if self.courier is None:
            return "ожидает курьера"
        return "передан курьеру"

    def delivery_cost(self) -> float:
        """Стоимость доставки с учётом веса и бесплатного порога."""
        if is_free_delivery(self.goods_sum):
            return 0.0
        return (
            zone_base_price(self.distance_km)
            + weight_surcharge(self.weight)
        )

    def total_to_pay(self) -> float:
        """Общая сумма к оплате: товары + доставка."""
        return self.goods_sum + self.delivery_cost()

    def delivery_minutes(self) -> int:
        """Полное время доставки: сборка + путь по зоне, мин."""
        return PREP_MINUTES + zone_travel_minutes(self.distance_km)

    def planned_delivery_at(self) -> datetime:
        """Плановое время вручения заказа."""
        return self.created_at + timedelta(minutes=self.delivery_minutes())

    def tracking_number(self) -> str:
        """Трек-номер заказа: дата + номер заказа."""
        return f"DLV-{self.created_at.strftime('%Y%m%d')}-{self.id}"

    def assign_courier(self, courier: Courier) -> None:
        """Закрепить курьера за заказом."""
        courier.take_order()
        self.courier = courier

    def cancel(self) -> None:
        """Отменить заказ и освободить назначенного курьера."""
        self.is_cancelled = True
        if self.courier is not None:
            self.courier.release()

    def __str__(self) -> str:
        """Вернуть строковое представление заказа."""
        courier_name = self.courier.name if self.courier else "не назначен"
        return (
            f"#{self.id:<4} {self.customer.name:<20} "
            f"{self.distance_km:>5} км  {self.weight:>5} кг  "
            f"курьер: {courier_name:<10} [{self.status}]"
        )


# --- Коллекция заказов --------------------------------------------------

def create_order(
    orders: list[Order],
    customer: Customer,
    couriers: list[Courier],
    distance_km: float,
    weight: float,
    goods_sum: float,
    payment_is_online: bool,
    created_at: datetime,
) -> Order:
    """Создать заказ, назначить свободного курьера и добавить в коллекцию.

    Курьер назначается только в рабочее время сервиса и только
    подходящего по весу типа. Если такого нет, заказ ожидает курьера.
    """
    next_id = max((order.id for order in orders), default=0) + 1
    order = Order(
        next_id, customer, distance_km, weight, goods_sum,
        payment_is_online, created_at,
    )
    if is_working_time(created_at):
        courier = find_available_courier(couriers, weight)
        if courier is not None:
            order.assign_courier(courier)
    orders.append(order)
    return order


def find_order_by_id(orders: list[Order], order_id: int) -> Order | None:
    """Найти заказ по идентификатору."""
    for order in orders:
        if order.id == order_id:
            return order
    return None


def find_orders(orders: list[Order], query: str) -> list[Order]:
    """Найти заказы по подстроке в имени или телефоне клиента."""
    return [order for order in orders if order.customer.matches(query)]


def active_orders(orders: list[Order]) -> Iterator[Order]:
    """Генератор неотменённых заказов."""
    for order in orders:
        if not order.is_cancelled:
            yield order


def filter_orders_by_zone(orders: list[Order], zone: str) -> list[Order]:
    """Отобрать активные заказы, попадающие в указанную зону доставки."""
    return [order for order in active_orders(orders) if order.zone == zone]


def sort_orders(orders: list[Order], key: str = "distance") -> list[Order]:
    """Отсортировать заказы по выбранному ключу.

    Поддерживаемые ключи: "distance", "weight", "goods_sum".
    """
    sort_keys = {
        "distance": lambda order: order.distance_km,
        "weight": lambda order: order.weight,
        "goods_sum": lambda order: order.goods_sum,
    }
    if key not in sort_keys:
        raise ValueError(f"Неизвестный ключ сортировки: {key}")
    return sorted(orders, key=sort_keys[key])


def order_statistics(orders: list[Order]) -> dict:
    """Собрать статистику по активным заказам: выручка, средний чек,
    количество заказов по зонам доставки.
    """
    active = list(active_orders(orders))
    count_by_zone: dict[str, int] = {}
    for order in active:
        count_by_zone[order.zone] = count_by_zone.get(order.zone, 0) + 1

    if not active:
        return {"count": 0, "total_revenue": 0.0, "average_check": 0.0,
                "count_by_zone": count_by_zone}

    total_revenue = sum(order.total_to_pay() for order in active)
    return {
        "count": len(active),
        "total_revenue": round(total_revenue, 2),
        "average_check": round(total_revenue / len(active), 2),
        "count_by_zone": count_by_zone,
    }


def cancel_order(orders: list[Order], order_id: int) -> bool:
    """Отменить активный заказ по идентификатору.

    Заказ не удаляется из коллекции, меняется только его состояние.
    Возвращает False, если заказ не найден или уже отменён.
    """
    order = find_order_by_id(orders, order_id)
    if order is None or order.is_cancelled:
        return False
    order.cancel()
    return True


def build_receipt(order: Order) -> str:
    """Собрать текст квитанции по заказу."""
    lines = ["=== Квитанция по заказу ==="]
    lines.append(f"Трек-номер:        {order.tracking_number()}")
    lines.append(
        f"Клиент:            {order.customer.name}, {order.customer.phone}"
    )
    lines.append(
        f"Зона доставки:     {order.zone} ({order.distance_km} км)"
    )
    lines.append(f"Вес заказа:        {order.weight} кг")

    if order.courier is not None:
        lines.append(
            f"Курьер:            {order.courier.name} ({order.courier.type})"
        )
    else:
        lines.append("Курьер:            не назначен")

    lines.append(f"Сумма товаров:     {round(order.goods_sum, 2)} руб.")

    if is_free_delivery(order.goods_sum):
        lines.append(
            "Доставка:          бесплатно (заказ от "
            f"{FREE_DELIVERY_FROM} руб.)"
        )
    else:
        lines.append(
            f"Доставка:          {round(order.delivery_cost(), 2)} руб."
        )
        surcharge = weight_surcharge(order.weight)
        if surcharge > 0.0:
            lines.append(
                f"  в т.ч. надбавка за вес: {round(surcharge, 2)} руб."
            )

    payment_name = payment_method_name(order.payment_is_online)
    lines.append(
        f"Итого к оплате:    {round(order.total_to_pay(), 2)} руб. "
        f"({payment_name})"
    )
    lines.append(
        "Заказ создан:      " + order.created_at.strftime("%d.%m.%Y %H:%M")
    )
    lines.append(
        "Плановая доставка: "
        + order.planned_delivery_at().strftime("%d.%m.%Y %H:%M")
        + f" (через {order.delivery_minutes()} мин)"
    )

    if order.is_cancelled:
        status = "отменён клиентом"
    else:
        status = order_status(order.created_at, order.courier is not None)
    lines.append("Статус заказа:     " + status)
    return "\n".join(lines)


def show_orders(orders: list[Order]) -> None:
    """Вывести список заказов."""
    if not orders:
        print("Заказов пока нет")
        return
    for order in orders:
        print(order)
