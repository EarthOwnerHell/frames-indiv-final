import json
from datetime import datetime

import storage
from models import Courier, Customer, Order


def test_save_and_load_restores_object_links(tmp_path):
    customer = Customer(1, "Иван Петров", "+7 900 111-22-33")
    courier = Courier(2, "Марат", "велокурьер", is_free=False)
    order = Order(10, customer, 6.2, 7.4, 1490.0, True,
                  datetime(2026, 9, 8, 19, 30), courier)

    customers_file = tmp_path / "customers.json"
    couriers_file = tmp_path / "couriers.json"
    orders_file = tmp_path / "orders.json"
    storage.save_customers(customers_file, [customer])
    storage.save_couriers(couriers_file, [courier])
    storage.save_orders(orders_file, [order])

    saved = json.loads(orders_file.read_text(encoding="utf-8"))
    assert saved[0]["customer_id"] == 1
    assert saved[0]["courier_id"] == 2

    customers = storage.load_customers(customers_file)
    couriers = storage.load_couriers(couriers_file)
    orders = storage.load_orders(orders_file, customers, couriers)
    loaded = orders[0]
    assert loaded.customer is customers[0]
    assert loaded.courier is couriers[0]
    assert loaded.created_at == datetime(2026, 9, 8, 19, 30)
    assert couriers[0].is_free is False


def test_load_orders_skips_unknown_customer(tmp_path):
    orders_file = tmp_path / "orders.json"
    orders_file.write_text(json.dumps([{
        "id": 1, "customer_id": 42, "courier_id": None,
        "distance_km": 1.0, "weight": 1.0, "goods_sum": 100.0,
        "payment_is_online": True, "created_at": "2026-09-08T19:30:00",
        "is_cancelled": False,
    }]), encoding="utf-8")
    assert storage.load_orders(orders_file, [], []) == []


def test_load_json_missing_or_broken_file(tmp_path):
    assert storage.load_json(tmp_path / "missing.json") == []
    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    assert storage.load_json(broken) == []
