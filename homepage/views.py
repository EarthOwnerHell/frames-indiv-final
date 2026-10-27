from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from db.database import fetch_all, fetch_one


def index(request: HttpRequest) -> HttpResponse:
    """Главная страница: описание сервиса, сводка и последние заказы."""
    latest_orders = fetch_all("""
        SELECT
            id,
            strftime('%d.%m.%Y %H:%M', created_at) AS created_at_display,
            goods_sum,
            CASE
                WHEN is_cancelled = 1 THEN 'отменён'
                WHEN courier_id IS NULL THEN 'ожидает курьера'
                ELSE 'передан курьеру'
            END AS status
        FROM orders
        ORDER BY created_at DESC
        LIMIT 3
    """)
    couriers_summary = fetch_one("""
        SELECT
            COUNT(*) AS couriers_count,
            SUM(is_free) AS free_count
        FROM couriers
    """)
    context = {
        "latest_orders": latest_orders,
        "couriers_summary": couriers_summary,
    }
    return render(request, "homepage/index.html", context)
