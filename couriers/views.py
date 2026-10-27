import math

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from db.database import fetch_all, fetch_one
from models.couriers import courier_type


def couriers(request: HttpRequest) -> HttpResponse:
    """Страница /couriers/: список курьеров из таблицы couriers."""
    couriers_list = fetch_all("""
        SELECT
            id,
            name,
            type,
            is_free
        FROM couriers
        ORDER BY name
    """)
    context = {
        "couriers": couriers_list,
    }
    return render(request, "couriers/courier_list.html", context)


def courier_detail(request: HttpRequest, courier_id: int) -> HttpResponse:
    """Страница /couriers/<id>/: карточка курьера и его заказы или 404."""
    courier = fetch_one("""
        SELECT
            id,
            name,
            type,
            is_free
        FROM couriers
        WHERE id = ?
    """, (courier_id,))
    courier_orders = []
    if courier is not None:
        courier_orders = fetch_all("""
            SELECT
                orders.id,
                customers.name AS customer_name,
                CASE
                    WHEN orders.is_cancelled = 1 THEN 'отменён'
                    WHEN orders.courier_id IS NULL THEN 'ожидает курьера'
                    ELSE 'передан курьеру'
                END AS status
            FROM orders
            JOIN customers
                ON orders.customer_id = customers.id
            WHERE orders.courier_id = ?
            ORDER BY orders.created_at DESC
        """, (courier_id,))
    context = {
        "courier": courier,
        "courier_orders": courier_orders,
    }
    return render(
        request,
        "couriers/courier_detail.html",
        context,
        status=404 if courier is None else 200,
    )


def available(request: HttpRequest) -> HttpResponse:
    """Страница /couriers/available/: подбор свободного курьера по весу.

    Тип курьера определяется правилом сервиса courier_type(), а поиск
    свободных курьеров этого типа выполняется SQL-запросом.
    """
    weight_text = request.GET.get("weight", "").strip().replace(",", ".")
    weight = None
    needed_type = None
    error = None
    couriers_list = []
    if weight_text:
        try:
            weight = float(weight_text)
        except ValueError:
            error = "Вес должен быть числом, например 7.5"
        else:
            if not math.isfinite(weight) or weight < 0:
                error = "Вес должен быть неотрицательным числом"
                weight = None
    if weight is not None:
        needed_type = courier_type(weight)
        couriers_list = fetch_all("""
            SELECT
                id,
                name,
                type
            FROM couriers
            WHERE type = ?
              AND is_free = 1
            ORDER BY name
        """, (needed_type,))
    context = {
        "weight_text": weight_text,
        "weight": weight,
        "needed_type": needed_type,
        "error": error,
        "couriers": couriers_list,
    }
    return render(request, "couriers/available.html", context)
