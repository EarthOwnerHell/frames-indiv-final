import os
from datetime import datetime

import django
import pytest

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "delivery.settings")
django.setup()

from django.test import Client  # noqa: E402
from django.test.utils import setup_test_environment  # noqa: E402

import storage  # noqa: E402
from models import Courier, Customer, Order  # noqa: E402

setup_test_environment()


@pytest.fixture
def client(tmp_path, monkeypatch):
    """Клиент Django с временными JSON-файлами данных."""
    customer = Customer(1, "Иван <b>Петров</b>", "+7 900 111-22-33")
    courier = Courier(2, "Марат", "велокурьер", is_free=False)
    order = Order(10, customer, 6.2, 7.4, 1490.0, True,
                  datetime(2026, 9, 8, 19, 30), courier)

    for name in ("CUSTOMERS_FILE", "COURIERS_FILE", "ORDERS_FILE"):
        monkeypatch.setattr(storage, name, str(tmp_path / f"{name}.json"))
    storage.save_customers(storage.CUSTOMERS_FILE, [customer])
    storage.save_couriers(storage.COURIERS_FILE, [courier])
    storage.save_orders(storage.ORDERS_FILE, [order])
    return Client()


@pytest.mark.parametrize("url", ["/", "/orders/", "/couriers/"])
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
