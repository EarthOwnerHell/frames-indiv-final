import os
from datetime import datetime

import django
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "delivery.settings")
django.setup()

from django.test import Client  # noqa: E402
from django.test.utils import setup_test_environment  # noqa: E402

import storage  # noqa: E402
from db import database, import_json  # noqa: E402
from models import Courier, Customer, Order  # noqa: E402

setup_test_environment()


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Клиент Django с временной базой SQLite, заполненной из JSON."""
    customer = Customer(1, "Иван <b>Петров</b>", "+7 900 111-22-33")
    courier = Courier(2, "Марат", "велокурьер", is_free=False)
    free_courier = Courier(3, "Ольга", "пеший курьер")
    order = Order(10, customer, 6.2, 7.4, 1490.0, True,
                  datetime(2026, 9, 8, 19, 30), courier)
    waiting = Order(11, customer, 2.0, 1.0, 300.0, False,
                    datetime(2026, 9, 9, 10, 0))

    for name in ("CUSTOMERS_FILE", "COURIERS_FILE", "ORDERS_FILE"):
        monkeypatch.setattr(storage, name, str(tmp_path / f"{name}.json"))
    storage.save_customers(storage.CUSTOMERS_FILE, [customer])
    storage.save_couriers(storage.COURIERS_FILE, [courier, free_courier])
    storage.save_orders(storage.ORDERS_FILE, [order, waiting])

    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "test.sqlite"))
    import_json.main()
    return Client()


@pytest.mark.parametrize("url", [
    "/", "/orders/", "/couriers/", "/orders/statistics/",
    "/couriers/available/",
])
def test_pages_open(client, url):
    response = client.get(url)
    assert response.status_code == 200
    assert "bootstrap" in response.content.decode()


def test_orders_page_lists_order(client):
    html = client.get("/orders/").content.decode()
    assert 'href="/orders/10/"' in html
    assert "передан курьеру" in html


def test_order_detail_shows_linked_objects(client):
    response = client.get("/orders/10/")
    html = response.content.decode()
    assert response.status_code == 200
    assert "+7 900 111-22-33" in html
    assert 'href="/couriers/2/"' in html
    assert "DLV-20260908-10" in html


def test_courier_detail_lists_courier_orders(client):
    html = client.get("/couriers/2/").content.decode()
    assert "Марат" in html
    assert 'href="/orders/10/"' in html
    assert "занят" in html


def test_customer_name_is_escaped(client):
    html = client.get("/orders/").content.decode()
    assert "<b>Петров</b>" not in html
    assert "&lt;b&gt;Петров&lt;/b&gt;" in html


@pytest.mark.parametrize("url", ["/orders/999/", "/couriers/999/"])
def test_unknown_id_returns_404(client, url):
    assert client.get(url).status_code == 404


@pytest.mark.parametrize("url, template", [
    ("/", "homepage/index.html"),
    ("/orders/", "orders/order_list.html"),
    ("/orders/10/", "orders/order_detail.html"),
    ("/couriers/", "couriers/courier_list.html"),
    ("/couriers/2/", "couriers/courier_detail.html"),
    ("/orders/statistics/", "orders/statistics.html"),
    ("/couriers/available/", "couriers/available.html"),
])
def test_pages_extend_base_template(client, url, template):
    names = [t.name for t in client.get(url).templates]
    assert template in names
    assert "base.html" in names
    assert "includes/navigation.html" in names


def test_base_template_links_static_files(client):
    html = client.get("/").content.decode()
    assert "/static/homepage/css/style.css" in html
    assert "/static/homepage/js/main.js" in html
    assert "/static/homepage/img/logo.png" in html


def test_not_found_page_uses_template(client):
    response = client.get("/orders/999/")
    assert "Заказ не найден" in response.content.decode()
    assert "orders/order_detail.html" in [t.name for t in response.templates]


def test_pages_show_current_database_data(client):
    conn = database.get_connection()
    conn.execute("UPDATE couriers SET name = 'Марат Иванов' WHERE id = 2")
    conn.commit()
    conn.close()
    assert "Марат Иванов" in client.get("/couriers/").content.decode()
    assert "Марат Иванов" in client.get("/orders/10/").content.decode()


def test_orders_page_shows_waiting_order_without_courier(client):
    html = client.get("/orders/").content.decode()
    assert 'href="/orders/11/"' in html
    assert "ожидает курьера" in html
    assert "не назначен" in html


@pytest.mark.parametrize("weight, expected", [
    ("1", "Ольга"),
    ("0,5", "Ольга"),
    ("7", "Свободных курьеров этого типа сейчас нет"),
    ("abc", "Вес должен быть числом"),
    ("-3", "Вес должен быть неотрицательным числом"),
    ("nan", "Вес должен быть неотрицательным числом"),
])
def test_available_couriers_by_weight(client, weight, expected):
    response = client.get("/couriers/available/", {"weight": weight})
    assert response.status_code == 200
    assert expected in response.content.decode()


def test_available_couriers_needs_no_weight(client):
    html = client.get("/couriers/available/").content.decode()
    assert "Нужен" not in html


def test_statistics_page_aggregates(client):
    response = client.get("/orders/statistics/")
    context = response.context
    assert context["summary"]["orders_count"] == 2
    assert context["summary"]["goods_total"] == 1790.0
    statuses = {row["status"]: row["orders_count"]
                for row in context["by_status"]}
    assert statuses == {"передан курьеру": 1, "ожидает курьера": 1}
    load = {row["name"]: row["orders_count"]
            for row in context["by_courier"]}
    assert load == {"Марат": 1, "Ольга": 0}
    assert [row["id"] for row in context["waiting_orders"]] == [11]
    assert [row["customer_name"]
            for row in context["regular_customers"]] == ["Иван <b>Петров</b>"]


def test_navigation_links_to_statistics(client):
    html = client.get("/").content.decode()
    assert 'href="/orders/statistics/"' in html
