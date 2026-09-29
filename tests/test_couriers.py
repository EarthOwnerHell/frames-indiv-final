from datetime import datetime

from models import Courier
from models.couriers import (
    courier_type,
    find_available_courier,
    find_courier_by_id,
    order_status,
)


def make_couriers():
    return [
        Courier(1, "Алексей", "пеший курьер"),
        Courier(2, "Марат", "велокурьер"),
    ]


def test_courier_creation():
    courier = Courier(1, "Алексей", "пеший курьер")
    assert courier.id == 1
    assert courier.name == "Алексей"
    assert courier.type == "пеший курьер"
    assert courier.is_free is True


def test_courier_str_shows_busy_state():
    courier = Courier(1, "Алексей", "пеший курьер")
    assert "свободен" in str(courier)
    courier.take_order()
    assert "занят" in str(courier)


def test_courier_take_order_and_release():
    courier = Courier(1, "Алексей", "пеший курьер")
    courier.take_order()
    assert courier.is_free is False
    courier.release()
    assert courier.is_free is True


def test_courier_is_suitable_for_weight():
    courier = Courier(2, "Марат", "велокурьер")
    assert courier.is_suitable_for(7.0)
    assert not courier.is_suitable_for(3.0)
    assert not courier.is_suitable_for(20.0)


def test_courier_from_data():
    data = {"id": 3, "name": "Сергей", "type": "автокурьер",
            "is_free": False}
    courier = Courier.from_data(data)
    assert courier.type == "автокурьер"
    assert courier.is_free is False


def test_courier_type_by_weight():
    assert courier_type(5.0) == "пеший курьер"
    assert courier_type(15.0) == "велокурьер"
    assert courier_type(15.1) == "автокурьер"


def test_find_available_courier_matches_weight_type():
    courier = find_available_courier(make_couriers(), 7.0)
    assert courier.name == "Марат"


def test_find_available_courier_skips_busy():
    couriers = make_couriers()
    couriers[1].take_order()
    assert find_available_courier(couriers, 7.0) is None


def test_find_courier_by_id():
    couriers = make_couriers()
    assert find_courier_by_id(couriers, 2) is couriers[1]
    assert find_courier_by_id(couriers, 99) is None


def test_order_status_outside_working_hours():
    moment = datetime(2026, 9, 15, 2, 0)
    assert order_status(moment, True) == (
        "отменён: сервис не работает в это время"
    )
