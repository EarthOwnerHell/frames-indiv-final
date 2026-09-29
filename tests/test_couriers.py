from datetime import datetime

import pytest

import couriers


def make_couriers():
    return [
        {"id": 1, "name": "Алексей", "type": "пеший курьер",
         "is_free": True},
        {"id": 2, "name": "Марат", "type": "велокурьер", "is_free": True},
    ]


def test_find_available_courier_matches_weight_type():
    courier_list = make_couriers()
    courier = couriers.find_available_courier(courier_list, 7.0)
    assert courier["name"] == "Марат"


def test_assign_courier_marks_busy_within_working_hours():
    courier_list = make_couriers()
    order = {"weight": 3.0, "courier_id": None}
    moment = datetime(2026, 9, 15, 12, 0)
    status = couriers.assign_courier(courier_list, order, moment)
    assert order["courier_id"] == 1
    assert courier_list[0]["is_free"] is False
    assert status == "передан курьеру, в пути к клиенту"


def test_assign_courier_outside_working_hours():
    courier_list = make_couriers()
    order = {"weight": 3.0, "courier_id": None}
    moment = datetime(2026, 9, 15, 2, 0)
    status = couriers.assign_courier(courier_list, order, moment)
    assert order["courier_id"] is None
    assert status == "отменён: сервис не работает в это время"


def test_release_courier_frees_it():
    courier_list = make_couriers()
    courier_list[0]["is_free"] = False
    couriers.release_courier(courier_list, 1)
    assert courier_list[0]["is_free"] is True


def test_release_courier_missing_id_raises_key_error():
    with pytest.raises(KeyError):
        couriers.release_courier(make_couriers(), 999)
