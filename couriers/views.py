from django.http import HttpRequest, HttpResponse
from django.utils.html import escape

import storage
from homepage.views import page
from models import Courier
from models.couriers import find_courier_by_id
from orders.views import order_status_badge


def busy_badge(courier: Courier) -> str:
    """HTML-бейдж занятости курьера."""
    if courier.is_free:
        return '<span class="badge bg-success">свободен</span>'
    return '<span class="badge bg-danger">занят</span>'


def couriers(request: HttpRequest) -> HttpResponse:
    """Страница /couriers/: список курьеров из data/couriers.json."""
    _, couriers_list, _ = storage.load_all()
    items = ""
    for courier in couriers_list:
        items += f"""
        <li class="list-group-item d-flex justify-content-between">
            <a href="/couriers/{courier.id}/">
                {escape(courier.name)} – {courier.type}
            </a>
            {busy_badge(courier)}
        </li>
        """
    if not items:
        items = '<li class="list-group-item">Курьеров пока нет</li>'
    content = f"""
    <h1>Курьеры</h1>
    <ul class="list-group">{items}</ul>
    """
    return HttpResponse(page("Курьеры", content))


def courier_detail(request: HttpRequest, courier_id: int) -> HttpResponse:
    """Страница /couriers/<id>/: карточка курьера и его заказы или 404."""
    _, couriers_list, orders_list = storage.load_all()
    courier = find_courier_by_id(couriers_list, courier_id)
    if courier is None:
        content = """
        <h1 class="text-danger">Курьер не найден</h1>
        <a href="/couriers/" class="btn btn-outline-secondary">
            ← к списку курьеров
        </a>
        """
        return HttpResponse(page("Курьер не найден", content), status=404)

    items = ""
    for order in orders_list:
        if order.courier is courier:
            items += f"""
            <li class="list-group-item d-flex justify-content-between">
                <a href="/orders/{order.id}/">
                    #{order.id} – {escape(order.customer.name)}
                </a>
                {order_status_badge(order)}
            </li>
            """
    if not items:
        items = '<li class="list-group-item">Заказов нет</li>'
    content = f"""
    <div class="card">
        <div class="card-body">
            <h5 class="card-title">{escape(courier.name)}
                {busy_badge(courier)}</h5>
            <p class="card-text"><strong>ID:</strong> {courier.id}</p>
            <p class="card-text">
                <strong>Тип:</strong> {courier.type}
            </p>
            <h6 class="mt-3">Заказы курьера</h6>
            <ul class="list-group mb-3">{items}</ul>
            <a href="/couriers/" class="btn btn-outline-secondary">
                ← к списку курьеров
            </a>
        </div>
    </div>
    """
    return HttpResponse(page(escape(courier.name), content))
