from django.http import HttpRequest, HttpResponse
from django.utils.html import escape

import storage
from homepage.views import page
from models import Order
from models.orders import find_order_by_id, payment_method_name

STATUS_BADGES = {
    "отменён": "bg-secondary",
    "ожидает курьера": "bg-warning text-dark",
    "передан курьеру": "bg-success",
}


def order_status_badge(order: Order) -> str:
    """HTML-бейдж с текущим состоянием заказа."""
    return (
        f'<span class="badge {STATUS_BADGES[order.status]}">'
        f"{order.status}</span>"
    )


def orders(request: HttpRequest) -> HttpResponse:
    """Страница /orders/: список заказов из data/orders.json."""
    _, _, orders_list = storage.load_all()
    rows = ""
    for order in orders_list:
        rows += f"""
        <tr>
            <td><a href="/orders/{order.id}/">#{order.id}</a></td>
            <td>{escape(order.customer.name)}</td>
            <td>{order.zone}</td>
            <td class="text-end">{round(order.total_to_pay(), 2)} руб.</td>
            <td>{order_status_badge(order)}</td>
        </tr>
        """
    if not rows:
        rows = '<tr><td colspan="5">Заказов пока нет</td></tr>'
    content = f"""
    <h1>Заказы</h1>
    <div class="table-responsive">
    <table class="table table-hover bg-white">
        <thead>
            <tr>
                <th>Номер</th><th>Клиент</th><th>Зона</th>
                <th class="text-end">К оплате</th><th>Статус</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    </div>
    """
    return HttpResponse(page("Заказы", content))


def order_detail(request: HttpRequest, order_id: int) -> HttpResponse:
    """Страница /orders/<id>/: карточка заказа или 404."""
    _, _, orders_list = storage.load_all()
    order = find_order_by_id(orders_list, order_id)
    if order is None:
        content = """
        <h1 class="text-danger">Заказ не найден</h1>
        <a href="/orders/" class="btn btn-outline-secondary">
            ← к списку заказов
        </a>
        """
        return HttpResponse(page("Заказ не найден", content), status=404)

    if order.courier is not None:
        courier = (
            f'<a href="/couriers/{order.courier.id}/">'
            f"{escape(order.courier.name)}</a> ({order.courier.type})"
        )
    else:
        courier = "не назначен"
    date_format = "%d.%m.%Y %H:%M"
    content = f"""
    <div class="card">
        <div class="card-body">
            <h5 class="card-title">Заказ #{order.id}
                {order_status_badge(order)}</h5>
            <p class="card-text text-muted">
                Трек-номер: {order.tracking_number()}
            </p>
            <dl class="row mb-0">
                <dt class="col-sm-4">Клиент</dt>
                <dd class="col-sm-8">{escape(order.customer.name)},
                    {escape(order.customer.phone)}</dd>
                <dt class="col-sm-4">Курьер</dt>
                <dd class="col-sm-8">{courier}</dd>
                <dt class="col-sm-4">Зона доставки</dt>
                <dd class="col-sm-8">{order.zone}
                    ({order.distance_km} км)</dd>
                <dt class="col-sm-4">Вес</dt>
                <dd class="col-sm-8">{order.weight} кг</dd>
                <dt class="col-sm-4">Сумма товаров</dt>
                <dd class="col-sm-8">{round(order.goods_sum, 2)} руб.</dd>
                <dt class="col-sm-4">Доставка</dt>
                <dd class="col-sm-8">
                    {round(order.delivery_cost(), 2)} руб.</dd>
                <dt class="col-sm-4">Итого к оплате</dt>
                <dd class="col-sm-8">{round(order.total_to_pay(), 2)} руб.
                    ({payment_method_name(order.payment_is_online)})</dd>
                <dt class="col-sm-4">Создан</dt>
                <dd class="col-sm-8">
                    {order.created_at.strftime(date_format)}</dd>
                <dt class="col-sm-4">Плановая доставка</dt>
                <dd class="col-sm-8">
                    {order.planned_delivery_at().strftime(date_format)}</dd>
            </dl>
            <a href="/orders/" class="btn btn-outline-secondary mt-3">
                ← к списку заказов
            </a>
        </div>
    </div>
    """
    return HttpResponse(page(f"Заказ #{order.id}", content))
