import sqlite3
from datetime import datetime

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from db.database import fetch_all, fetch_one
from models import Courier, Customer, Order
from models.orders import payment_method_name

# Минимальное число активных заказов, начиная с которого клиент
# считается постоянным (строго больше этого значения)
REGULAR_CUSTOMER_MIN_ORDERS = 1


def order_from_row(row: sqlite3.Row) -> Order:
    """Собрать объект Order со связанными Customer и Courier из строки.

    Расчёты по заказу (зона, стоимость доставки, сроки, трек-номер)
    остаются в методах Order и не дублируются в SQL.
    """
    customer = Customer(
        row["customer_id"], row["customer_name"], row["customer_phone"]
    )
    courier = None
    if row["courier_id"] is not None:
        courier = Courier(
            row["courier_id"],
            row["courier_name"],
            row["courier_type"],
            is_free=bool(row["courier_is_free"]),
        )
    order = Order(
        order_id=row["id"],
        customer=customer,
        distance_km=row["distance_km"],
        weight=row["weight"],
        goods_sum=row["goods_sum"],
        payment_is_online=bool(row["payment_is_online"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        courier=courier,
    )
    order.is_cancelled = bool(row["is_cancelled"])
    return order


def orders(request: HttpRequest) -> HttpResponse:
    """Страница /orders/: заказы с именами клиента и курьера."""
    orders_list = fetch_all("""
        SELECT
            orders.id,
            strftime('%d.%m.%Y %H:%M', orders.created_at)
                AS created_at_display,
            customers.name AS customer_name,
            couriers.name AS courier_name,
            orders.goods_sum,
            CASE
                WHEN orders.is_cancelled = 1 THEN 'отменён'
                WHEN orders.courier_id IS NULL THEN 'ожидает курьера'
                ELSE 'передан курьеру'
            END AS status
        FROM orders
        JOIN customers
            ON orders.customer_id = customers.id
        LEFT JOIN couriers
            ON orders.courier_id = couriers.id
        ORDER BY orders.created_at DESC
    """)
    context = {
        "orders": orders_list,
    }
    return render(request, "orders/order_list.html", context)


def order_detail(request: HttpRequest, order_id: int) -> HttpResponse:
    """Страница /orders/<id>/: карточка заказа или 404."""
    row = fetch_one("""
        SELECT
            orders.id,
            orders.distance_km,
            orders.weight,
            orders.goods_sum,
            orders.payment_is_online,
            orders.created_at,
            orders.is_cancelled,
            customers.id AS customer_id,
            customers.name AS customer_name,
            customers.phone AS customer_phone,
            couriers.id AS courier_id,
            couriers.name AS courier_name,
            couriers.type AS courier_type,
            couriers.is_free AS courier_is_free
        FROM orders
        JOIN customers
            ON orders.customer_id = customers.id
        LEFT JOIN couriers
            ON orders.courier_id = couriers.id
        WHERE orders.id = ?
    """, (order_id,))
    order = order_from_row(row) if row is not None else None
    context = {
        "order": order,
        "payment_method": (
            payment_method_name(order.payment_is_online) if order else ""
        ),
    }
    return render(
        request,
        "orders/order_detail.html",
        context,
        status=404 if order is None else 200,
    )


def statistics(request: HttpRequest) -> HttpResponse:
    """Страница /orders/statistics/: сводные показатели по заказам."""
    summary = fetch_one("""
        SELECT
            COUNT(*) AS orders_count,
            ROUND(SUM(goods_sum), 2) AS goods_total,
            ROUND(AVG(goods_sum), 2) AS goods_avg
        FROM orders
        WHERE is_cancelled = 0
    """)
    by_status = fetch_all("""
        SELECT
            CASE
                WHEN is_cancelled = 1 THEN 'отменён'
                WHEN courier_id IS NULL THEN 'ожидает курьера'
                ELSE 'передан курьеру'
            END AS status,
            COUNT(*) AS orders_count
        FROM orders
        GROUP BY status
        ORDER BY orders_count DESC
    """)
    by_courier = fetch_all("""
        SELECT
            couriers.id,
            couriers.name,
            couriers.type,
            COUNT(orders.id) AS orders_count,
            COUNT(CASE WHEN orders.is_cancelled = 0 THEN 1 END)
                AS active_count
        FROM couriers
        LEFT JOIN orders
            ON couriers.id = orders.courier_id
        GROUP BY couriers.id, couriers.name, couriers.type
        ORDER BY orders_count DESC, couriers.name
    """)
    by_customer = fetch_all("""
        SELECT
            customers.name AS customer_name,
            COUNT(orders.id) AS orders_count,
            ROUND(COALESCE(SUM(orders.goods_sum), 0), 2) AS goods_total
        FROM customers
        LEFT JOIN orders
            ON customers.id = orders.customer_id
            AND orders.is_cancelled = 0
        GROUP BY customers.id, customers.name
        ORDER BY goods_total DESC
    """)
    regular_customers = fetch_all("""
        SELECT
            customers.name AS customer_name,
            COUNT(orders.id) AS orders_count
        FROM customers
        JOIN orders
            ON customers.id = orders.customer_id
        WHERE orders.is_cancelled = 0
        GROUP BY customers.id, customers.name
        HAVING COUNT(orders.id) > ?
        ORDER BY orders_count DESC
    """, (REGULAR_CUSTOMER_MIN_ORDERS,))
    waiting_orders = fetch_all("""
        SELECT
            orders.id,
            strftime('%d.%m.%Y %H:%M', orders.created_at)
                AS created_at_display,
            customers.name AS customer_name,
            orders.weight
        FROM orders
        JOIN customers
            ON orders.customer_id = customers.id
        WHERE orders.courier_id IS NULL
          AND orders.is_cancelled = 0
        ORDER BY orders.created_at
    """)
    context = {
        "summary": summary,
        "by_status": by_status,
        "by_courier": by_courier,
        "by_customer": by_customer,
        "regular_customers": regular_customers,
        "regular_min_orders": REGULAR_CUSTOMER_MIN_ORDERS,
        "waiting_orders": waiting_orders,
    }
    return render(request, "orders/statistics.html", context)
