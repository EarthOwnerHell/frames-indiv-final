import os
from datetime import datetime

import couriers
import orders
import storage
import utils

DATA_DIR = "data"
ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")
COURIERS_FILE = os.path.join(DATA_DIR, "couriers.json")

MENU = """
=== Сервис доставки заказов ===

1. Показать заказы
2. Показать курьеров
3. Оформить новый заказ
4. Отменить заказ
5. Найти заказ по имени или телефону
6. Отсортировать заказы
7. Статистика по заказам
0. Выход
"""


def build_receipt(order: dict, courier: dict | None) -> str:
    """Собрать текст квитанции по заказу."""
    created_at = datetime.fromisoformat(order["created_at"])
    distance_km = order["distance_km"]
    weight = order["weight"]
    goods_sum = order["goods_sum"]

    lines = ["=== Квитанция по заказу ==="]
    lines.append(
        "Трек-номер:        "
        + orders.tracking_number(created_at, order["id"])
    )
    lines.append(
        f"Клиент:            {order['client_name']}, "
        f"{order['client_phone']}"
    )
    lines.append(
        "Зона доставки:     "
        f"{orders.delivery_zone(distance_km)} ({distance_km} км)"
    )
    lines.append(f"Вес заказа:        {weight} кг")

    if courier is not None:
        lines.append(
            f"Курьер:            {courier['name']} ({courier['type']})"
        )
    else:
        lines.append("Курьер:            не назначен")

    lines.append(f"Сумма товаров:     {round(goods_sum, 2)} руб.")

    if orders.is_free_delivery(goods_sum):
        lines.append(
            "Доставка:          бесплатно (заказ от "
            f"{orders.FREE_DELIVERY_FROM} руб.)"
        )
    else:
        cost = orders.delivery_cost(distance_km, weight, goods_sum)
        lines.append(f"Доставка:          {round(cost, 2)} руб.")
        surcharge = orders.weight_surcharge(weight)
        if surcharge > 0.0:
            lines.append(
                f"  в т.ч. надбавка за вес: {round(surcharge, 2)} руб."
            )

    total = orders.total_to_pay(distance_km, weight, goods_sum)
    payment_name = orders.payment_method_name(order["payment_is_online"])
    lines.append(
        f"Итого к оплате:    {round(total, 2)} руб. ({payment_name})"
    )
    lines.append(
        "Заказ создан:      " + created_at.strftime("%d.%m.%Y %H:%M")
    )
    planned = orders.planned_delivery_at(created_at, distance_km)
    minutes = orders.delivery_minutes(distance_km)
    lines.append(
        "Плановая доставка: " + planned.strftime("%d.%m.%Y %H:%M")
        + f" (через {minutes} мин)"
    )

    courier_is_free = courier is not None
    status = couriers.order_status(created_at, courier_is_free)
    if order["cancelled"]:
        status = "отменён клиентом"
    lines.append("Статус заказа:     " + status)
    return "\n".join(lines)


def show_orders(order_list: list[dict], courier_list: list[dict]) -> None:
    """Вывести список заказов в виде таблицы."""
    if not order_list:
        print("Заказов пока нет")
        return
    for order in order_list:
        courier = couriers.find_courier_by_id(
            courier_list, order["courier_id"]
        )
        courier_name = courier["name"] if courier else "не назначен"
        status = "отменён" if order["cancelled"] else "активен"
        print(
            f"#{order['id']:<4} {order['client_name']:<20} "
            f"{order['distance_km']:>5} км  {order['weight']:>5} кг  "
            f"курьер: {courier_name:<10} [{status}]"
        )


def show_couriers(courier_list: list[dict]) -> None:
    """Вывести список курьеров и их занятость."""
    for courier in courier_list:
        busy_state = "свободен" if courier["is_free"] else "занят"
        print(
            f"#{courier['id']} {courier['name']:<10} "
            f"{courier['type']:<14} [{busy_state}]"
        )


def create_order(order_list: list[dict], courier_list: list[dict]) -> None:
    """Оформить новый заказ: ввод данных, расчёт и назначение курьера."""
    client_name = utils.input_nonempty("Имя клиента: ")
    client_phone = utils.input_nonempty("Телефон клиента: ")
    distance_km = utils.input_float("Расстояние до клиента, км: ")
    weight = utils.input_float("Вес заказа, кг: ")
    goods_sum = utils.input_float("Сумма товаров, руб.: ")
    payment_is_online = utils.input_yes_no("Оплата онлайн?")
    created_at = datetime.now()

    order = orders.add_order(
        order_list, client_name, client_phone, distance_km, weight,
        goods_sum, payment_is_online, created_at,
    )
    couriers.assign_courier(courier_list, order, created_at)
    courier = couriers.find_courier_by_id(
        courier_list, order["courier_id"]
    )
    print()
    print(build_receipt(order, courier))


def cancel_order_action(
    order_list: list[dict], courier_list: list[dict]
) -> None:
    """Отменить заказ по номеру, освободив назначенного курьера."""
    order_id = utils.input_int("Номер заказа для отмены: ")
    try:
        order = orders.cancel_order(order_list, order_id)
    except KeyError as error:
        print(error)
        return
    if order["courier_id"] is not None:
        couriers.release_courier(courier_list, order["courier_id"])
    print(f"Заказ #{order_id} отменён")


def find_order_action(order_list: list[dict]) -> None:
    """Найти заказы по подстроке в имени или телефоне клиента."""
    query = utils.input_nonempty("Имя или телефон клиента: ")
    found = orders.find_orders(order_list, query)
    if not found:
        print("Ничего не найдено")
        return
    for order in found:
        print(f"#{order['id']} {order['client_name']}, "
              f"{order['client_phone']}")


def sort_orders_action(
    order_list: list[dict], courier_list: list[dict]
) -> None:
    """Вывести заказы, отсортированные по выбранному полю."""
    print("Сортировать по: 1 - расстояние, 2 - вес, 3 - сумма товаров")
    choice = utils.input_nonempty("Выберите вариант: ")
    key_by_choice = {"1": "distance", "2": "weight", "3": "goods_sum"}
    key = key_by_choice.get(choice)
    if key is None:
        print("Неверный выбор")
        return
    show_orders(orders.sort_orders(order_list, key), courier_list)


def show_statistics(order_list: list[dict]) -> None:
    """Вывести статистику по активным заказам."""
    stats = orders.order_statistics(order_list)
    print(f"Активных заказов:  {stats['count']}")
    print(f"Общая выручка:     {stats['total_revenue']} руб.")
    print(f"Средний чек:       {stats['average_check']} руб.")
    print("По зонам доставки:")
    for zone, count in stats["count_by_zone"].items():
        print(f"  {zone}: {count}")


def main() -> None:
    """Точка запуска приложения: цикл меню."""
    order_list = storage.load_json(ORDERS_FILE)
    courier_list = storage.load_json(COURIERS_FILE)

    actions = {
        "1": lambda: show_orders(order_list, courier_list),
        "2": lambda: show_couriers(courier_list),
        "3": lambda: create_order(order_list, courier_list),
        "4": lambda: cancel_order_action(order_list, courier_list),
        "5": lambda: find_order_action(order_list),
        "6": lambda: sort_orders_action(order_list, courier_list),
        "7": lambda: show_statistics(order_list),
    }

    while True:
        print(MENU)
        choice = input("Выберите действие: ").strip()
        if choice == "0":
            break
        action = actions.get(choice)
        if action is None:
            print("Неверный выбор, попробуйте снова")
            continue
        action()
        storage.save_json(ORDERS_FILE, order_list)
        storage.save_json(COURIERS_FILE, courier_list)

    print("До свидания!")


if __name__ == "__main__":
    main()
