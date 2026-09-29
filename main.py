from datetime import datetime

import storage
import utils
from models import Courier, Customer, Order
from models.couriers import show_couriers
from models.customers import (
    add_customer,
    find_customer,
    find_customer_by_phone,
    show_customers,
)
from models.orders import (
    build_receipt,
    cancel_order,
    create_order,
    find_orders,
    order_statistics,
    show_orders,
    sort_orders,
)

MENU = """
=== Сервис доставки заказов ===

1. Показать заказы
2. Показать курьеров
3. Показать клиентов
4. Оформить новый заказ
5. Отменить заказ
6. Найти заказ по имени или телефону
7. Найти клиента
8. Отсортировать заказы
9. Статистика по заказам
0. Выход
"""


def select_customer(customers: list[Customer]) -> Customer:
    """Найти клиента по телефону или зарегистрировать нового."""
    phone = utils.input_nonempty("Телефон клиента: ")
    customer = find_customer_by_phone(customers, phone)
    if customer is not None:
        print(f"Клиент найден: {customer}")
        return customer
    name = utils.input_nonempty("Новый клиент. Имя: ")
    customer = add_customer(customers, name, phone)
    print(f"Клиент зарегистрирован: {customer}")
    return customer


def create_new_order(
    orders: list[Order],
    customers: list[Customer],
    couriers: list[Courier],
) -> None:
    """Оформить новый заказ: выбор клиента, ввод данных, расчёт."""
    customer = select_customer(customers)
    distance_km = utils.input_float("Расстояние до клиента, км: ")
    weight = utils.input_float("Вес заказа, кг: ")
    goods_sum = utils.input_float("Сумма товаров, руб.: ")
    payment_is_online = utils.input_yes_no("Оплата онлайн?")

    order = create_order(
        orders, customer, couriers, distance_km, weight, goods_sum,
        payment_is_online, datetime.now(),
    )
    print()
    print(build_receipt(order))


def cancel_order_action(orders: list[Order]) -> None:
    """Отменить заказ по номеру; курьер освобождается автоматически."""
    order_id = utils.input_int("Номер заказа для отмены: ")
    if cancel_order(orders, order_id):
        print(f"Заказ #{order_id} отменён")
    else:
        print(f"Заказ #{order_id} не найден или уже отменён")


def find_order_action(orders: list[Order]) -> None:
    """Найти заказы по подстроке в имени или телефоне клиента."""
    query = utils.input_nonempty("Имя или телефон клиента: ")
    found = find_orders(orders, query)
    if not found:
        print("Ничего не найдено")
        return
    show_orders(found)


def find_customer_action(customers: list[Customer]) -> None:
    """Найти клиентов по подстроке в имени или телефоне."""
    query = utils.input_nonempty("Имя или телефон клиента: ")
    found = find_customer(customers, query)
    if not found:
        print("Ничего не найдено")
        return
    show_customers(found)


def sort_orders_action(orders: list[Order]) -> None:
    """Вывести заказы, отсортированные по выбранному полю."""
    print("Сортировать по: 1 - расстояние, 2 - вес, 3 - сумма товаров")
    choice = utils.input_nonempty("Выберите вариант: ")
    key_by_choice = {"1": "distance", "2": "weight", "3": "goods_sum"}
    key = key_by_choice.get(choice)
    if key is None:
        print("Неверный выбор")
        return
    show_orders(sort_orders(orders, key))


def show_statistics(orders: list[Order]) -> None:
    """Вывести статистику по активным заказам."""
    stats = order_statistics(orders)
    print(f"Активных заказов:  {stats['count']}")
    print(f"Общая выручка:     {stats['total_revenue']} руб.")
    print(f"Средний чек:       {stats['average_check']} руб.")
    print("По зонам доставки:")
    for zone, count in stats["count_by_zone"].items():
        print(f"  {zone}: {count}")


def save_all(
    orders: list[Order],
    customers: list[Customer],
    couriers: list[Courier],
) -> None:
    """Сохранить все коллекции объектов в JSON-файлы."""
    storage.save_customers(storage.CUSTOMERS_FILE, customers)
    storage.save_couriers(storage.COURIERS_FILE, couriers)
    storage.save_orders(storage.ORDERS_FILE, orders)


def main() -> None:
    """Точка запуска приложения: загрузка данных и цикл меню."""
    customers, couriers, orders = storage.load_all()

    actions = {
        "1": lambda: show_orders(orders),
        "2": lambda: show_couriers(couriers),
        "3": lambda: show_customers(customers),
        "4": lambda: create_new_order(orders, customers, couriers),
        "5": lambda: cancel_order_action(orders),
        "6": lambda: find_order_action(orders),
        "7": lambda: find_customer_action(customers),
        "8": lambda: sort_orders_action(orders),
        "9": lambda: show_statistics(orders),
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
        save_all(orders, customers, couriers)

    print("До свидания!")


if __name__ == "__main__":
    main()
