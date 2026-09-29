from datetime import datetime

import pytest

from models import Courier, Customer, Order
from models.orders import (
    OVERWEIGHT_RATE,
    cancel_order,
    create_order,
    filter_orders_by_zone,
    find_orders,
    order_statistics,
    sort_orders,
    weight_surcharge,
)

WORK_TIME = datetime(2026, 9, 15, 12, 0)
NIGHT_TIME = datetime(2026, 9, 15, 2, 0)


def make_customer():
    return Customer(1, "Иван Петров", "+7 900 111-22-33")


def make_couriers():
    return [
        Courier(1, "Алексей", "пеший курьер"),
        Courier(2, "Марат", "велокурьер"),
    ]


def make_order(distance_km=2.0, weight=3.0, goods_sum=500.0):
    return Order(1, make_customer(), distance_km, weight, goods_sum,
                 True, WORK_TIME)


def test_order_creation_links_customer():
    customer = make_customer()
    order = Order(1, customer, 2.0, 3.0, 500.0, True, WORK_TIME)
    assert order.id == 1
    assert order.customer is customer
    assert order.courier is None
    assert order.is_cancelled is False
    assert order.customer.name == "Иван Петров"


def test_order_rejects_negative_values():
    with pytest.raises(ValueError):
        make_order(weight=-1.0)


def test_order_validate_amount_is_static():
    assert Order.validate_amount(0.0)
    assert not Order.validate_amount(-0.5)


def test_order_delivery_cost_and_total():
    order = make_order(distance_km=6.2, weight=12.0, goods_sum=1000.0)
    assert order.delivery_cost() == 249.0 + 2 * OVERWEIGHT_RATE
    assert order.total_to_pay() == 1000.0 + order.delivery_cost()


def test_order_free_delivery_above_threshold():
    assert make_order(goods_sum=2500.0).delivery_cost() == 0.0


def test_order_zone_and_tracking_number():
    order = make_order(distance_km=9.0)
    assert order.zone == "Пригород"
    assert order.tracking_number() == "DLV-20260915-1"


def test_order_str_and_status():
    order = make_order()
    assert order.status == "ожидает курьера"
    assert "Иван Петров" in str(order)
    order.cancel()
    assert order.status == "отменён"
    assert "[отменён]" in str(order)


def test_weight_surcharge_applies_above_limit():
    assert weight_surcharge(12.0) == 2 * OVERWEIGHT_RATE


def test_create_order_assigns_suitable_courier():
    orders, couriers = [], make_couriers()
    order = create_order(orders, make_customer(), couriers,
                         2.0, 7.0, 500.0, True, WORK_TIME)
    assert orders == [order]
    assert order.courier is couriers[1]
    assert couriers[1].is_free is False
    assert order.status == "передан курьеру"


def test_create_order_outside_working_hours_has_no_courier():
    orders, couriers = [], make_couriers()
    order = create_order(orders, make_customer(), couriers,
                         2.0, 3.0, 500.0, True, NIGHT_TIME)
    assert order.courier is None
    assert couriers[0].is_free is True


def test_busy_courier_is_not_assigned_until_order_cancelled():
    orders, couriers = [], make_couriers()
    customer = make_customer()
    first = create_order(orders, customer, couriers,
                         2.0, 7.0, 500.0, True, WORK_TIME)
    second = create_order(orders, customer, couriers,
                          2.0, 7.0, 500.0, True, WORK_TIME)
    assert second.courier is None

    assert cancel_order(orders, first.id)
    third = create_order(orders, customer, couriers,
                         2.0, 7.0, 500.0, True, WORK_TIME)
    assert third.courier is couriers[1]


def test_cancel_order_keeps_order_in_collection():
    orders, couriers = [], make_couriers()
    order = create_order(orders, make_customer(), couriers,
                         2.0, 3.0, 500.0, True, WORK_TIME)
    assert cancel_order(orders, order.id)
    assert order in orders
    assert order.is_cancelled
    assert couriers[0].is_free is True


def test_cancel_order_twice_or_missing_returns_false():
    orders, couriers = [], make_couriers()
    order = create_order(orders, make_customer(), couriers,
                         2.0, 3.0, 500.0, True, WORK_TIME)
    assert cancel_order(orders, order.id)
    assert not cancel_order(orders, order.id)
    assert not cancel_order(orders, 999)


def test_find_orders_by_customer_phone():
    orders = []
    create_order(orders, make_customer(), [], 2.0, 3.0, 500.0,
                 True, WORK_TIME)
    assert len(find_orders(orders, "111-22-33")) == 1
    assert find_orders(orders, "нет такого") == []


def test_sort_and_filter_orders():
    orders = []
    customer = make_customer()
    far = create_order(orders, customer, [], 9.0, 1.0, 100.0,
                       True, WORK_TIME)
    near = create_order(orders, customer, [], 1.0, 1.0, 100.0,
                        True, WORK_TIME)
    assert sort_orders(orders, "distance") == [near, far]
    assert filter_orders_by_zone(orders, "Центр") == [near]
    with pytest.raises(ValueError):
        sort_orders(orders, "unknown")


def test_order_statistics_ignores_cancelled():
    orders = []
    customer = make_customer()
    create_order(orders, customer, [], 2.0, 1.0, 500.0, True, WORK_TIME)
    cancelled = create_order(orders, customer, [], 2.0, 1.0, 900.0,
                             True, WORK_TIME)
    cancelled.cancel()
    stats = order_statistics(orders)
    assert stats["count"] == 1
    assert stats["total_revenue"] == 500.0 + 149.0
    assert stats["count_by_zone"] == {"Центр": 1}
