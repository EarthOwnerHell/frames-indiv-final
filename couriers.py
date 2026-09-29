"""Курьеры: подбор типа, проверка доступности и назначение на заказ.

Функции courier_type, is_working_time, is_courier_assigned и
order_status перенесены из ПР1 без изменений логики.
"""

from datetime import datetime

WORK_START_HOUR = 8
WORK_END_HOUR = 23


def courier_type(weight: float) -> str:
    """Тип курьера, необходимый для заказа данного веса."""
    if weight <= 5.0:
        return "пеший курьер"
    if weight <= 15.0:
        return "велокурьер"
    return "автокурьер"


def is_working_time(moment: datetime) -> bool:
    """Попадает ли момент времени в рабочие часы сервиса."""
    return WORK_START_HOUR <= moment.hour < WORK_END_HOUR


def is_courier_assigned(moment: datetime, courier_is_free: bool) -> bool:
    """Можно ли назначить курьера: рабочее время и есть свободный курьер."""
    return is_working_time(moment) and courier_is_free


def order_status(moment: datetime, courier_is_free: bool) -> str:
    """Текущий статус заказа на момент оформления."""
    if not is_working_time(moment):
        return "отменён: сервис не работает в это время"
    if not is_courier_assigned(moment, courier_is_free):
        return "ожидает свободного курьера"
    return "передан курьеру, в пути к клиенту"


# --- Коллекция курьеров ---------------------------------------------------

def find_available_courier(
    couriers: list[dict], weight: float
) -> dict | None:
    """Найти первого свободного курьера подходящего типа для веса заказа."""
    required_type = courier_type(weight)
    for courier in couriers:
        if courier["type"] == required_type and courier["is_free"]:
            return courier
    return None


def assign_courier(
    couriers: list[dict], order: dict, moment: datetime
) -> str:
    """Назначить свободного курьера на заказ и вернуть статус заказа.

    При успешном назначении заказ получает courier_id, курьер
    помечается занятым (is_free = False).
    """
    courier = find_available_courier(couriers, order["weight"])
    courier_is_free = courier is not None and is_working_time(moment)
    if courier_is_free:
        courier["is_free"] = False
        order["courier_id"] = courier["id"]
    return order_status(moment, courier_is_free)


def release_courier(couriers: list[dict], courier_id: int) -> None:
    """Освободить курьера после доставки или отмены заказа.

    Вызывает KeyError, если курьер с указанным id не найден.
    """
    for courier in couriers:
        if courier["id"] == courier_id:
            courier["is_free"] = True
            return
    raise KeyError(f"Курьер с id={courier_id} не найден")


def find_courier_by_id(
    couriers: list[dict], courier_id: int
) -> dict | None:
    """Найти курьера по идентификатору."""
    for courier in couriers:
        if courier["id"] == courier_id:
            return courier
    return None
