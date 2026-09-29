from datetime import datetime

import pytest

import orders


def test_add_order_assigns_incremental_id():
    order_list = []
    order = orders.add_order(
        order_list, "Иван Петров", "+7 900 000-00-00",
        distance_km=2.0, weight=3.0, goods_sum=500.0,
        payment_is_online=True, created_at=datetime(2026, 9, 15, 10, 0),
    )
    assert order["id"] == 1
    assert order_list[0]["client_name"] == "Иван Петров"


def test_find_orders_by_phone_substring():
    order_list = []
    orders.add_order(
        order_list, "Иван Петров", "+7 900 111-22-33",
        distance_km=2.0, weight=3.0, goods_sum=500.0,
        payment_is_online=True, created_at=datetime(2026, 9, 15, 10, 0),
    )
    found = orders.find_orders(order_list, "111-22-33")
    assert len(found) == 1


def test_delivery_cost_is_free_above_threshold():
    assert orders.delivery_cost(6.2, 7.4, 2500.0) == 0.0


def test_weight_surcharge_applies_above_limit():
    assert orders.weight_surcharge(12.0) == 2 * orders.OVERWEIGHT_RATE


def test_cancel_order_marks_cancelled():
    order_list = []
    order = orders.add_order(
        order_list, "Иван Петров", "+7 900 000-00-00",
        distance_km=2.0, weight=3.0, goods_sum=500.0,
        payment_is_online=True, created_at=datetime(2026, 9, 15, 10, 0),
    )
    cancelled = orders.cancel_order(order_list, order["id"])
    assert cancelled["cancelled"] is True


def test_cancel_order_missing_id_raises_key_error():
    with pytest.raises(KeyError):
        orders.cancel_order([], 999)


def test_sort_orders_by_distance():
    order_list = []
    orders.add_order(
        order_list, "Клиент А", "+7 900 000-00-01",
        distance_km=9.0, weight=1.0, goods_sum=100.0,
        payment_is_online=True, created_at=datetime(2026, 9, 15, 10, 0),
    )
    orders.add_order(
        order_list, "Клиент Б", "+7 900 000-00-02",
        distance_km=1.0, weight=1.0, goods_sum=100.0,
        payment_is_online=True, created_at=datetime(2026, 9, 15, 10, 0),
    )
    sorted_orders = orders.sort_orders(order_list, "distance")
    assert sorted_orders[0]["client_name"] == "Клиент Б"
