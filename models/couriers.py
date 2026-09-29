"""Курьеры: класс Courier и функции работы с коллекцией курьеров.

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


class Courier:
    """Курьер сервиса доставки.

    Занятость курьера хранится в закрытом атрибуте _is_free и меняется
    только методами take_order() и release().
    """

    def __init__(
        self,
        courier_id: int,
        name: str,
        courier_kind: str,
        is_free: bool = True,
    ) -> None:
        """Создать объект курьера."""
        self.id = courier_id
        self.name = name
        self.type = courier_kind
        self._is_free = is_free

    @classmethod
    def from_data(cls, data: dict) -> "Courier":
        """Создать курьера из словаря, прочитанного из JSON."""
        return cls(data["id"], data["name"], data["type"], data["is_free"])

    @property
    def is_free(self) -> bool:
        """Свободен ли курьер (только для чтения)."""
        return self._is_free

    def is_suitable_for(self, weight: float) -> bool:
        """Подходит ли курьер по типу для заказа данного веса."""
        return self.type == courier_type(weight)

    def take_order(self) -> None:
        """Принять заказ в работу: курьер становится занятым."""
        self._is_free = False

    def release(self) -> None:
        """Освободить курьера после доставки или отмены заказа."""
        self._is_free = True

    def __str__(self) -> str:
        """Вернуть строковое представление курьера."""
        busy_state = "свободен" if self._is_free else "занят"
        return f"#{self.id} {self.name:<10} {self.type:<14} [{busy_state}]"


def find_available_courier(
    couriers: list[Courier], weight: float
) -> Courier | None:
    """Найти первого свободного курьера подходящего типа для веса заказа."""
    for courier in couriers:
        if courier.is_free and courier.is_suitable_for(weight):
            return courier
    return None


def find_courier_by_id(
    couriers: list[Courier], courier_id: int | None
) -> Courier | None:
    """Найти курьера по идентификатору."""
    for courier in couriers:
        if courier.id == courier_id:
            return courier
    return None


def show_couriers(couriers: list[Courier]) -> None:
    """Вывести список курьеров и их занятость."""
    for courier in couriers:
        print(courier)
