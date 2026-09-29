"""Клиенты: класс Customer и функции работы с коллекцией клиентов."""


class Customer:
    """Клиент сервиса доставки."""

    def __init__(self, customer_id: int, name: str, phone: str) -> None:
        """Создать объект клиента."""
        self.id = customer_id
        self.name = name
        self.phone = phone

    @classmethod
    def from_data(cls, data: dict) -> "Customer":
        """Создать клиента из словаря, прочитанного из JSON."""
        return cls(data["id"], data["name"], data["phone"])

    def matches(self, query: str) -> bool:
        """Проверить, встречается ли подстрока в имени или телефоне."""
        query_lower = query.lower()
        return (
            query_lower in self.name.lower()
            or query_lower in self.phone.lower()
        )

    def __str__(self) -> str:
        """Вернуть строковое представление клиента."""
        return f"#{self.id} {self.name}, {self.phone}"


def add_customer(
    customers: list[Customer], name: str, phone: str
) -> Customer:
    """Создать клиента, добавить его в коллекцию и вернуть.

    Идентификатор формируется как максимальный существующий id + 1.
    """
    next_id = max((customer.id for customer in customers), default=0) + 1
    customer = Customer(next_id, name, phone)
    customers.append(customer)
    return customer


def find_customer(customers: list[Customer], query: str) -> list[Customer]:
    """Найти клиентов по подстроке в имени или телефоне."""
    return [customer for customer in customers if customer.matches(query)]


def find_customer_by_id(
    customers: list[Customer], customer_id: int
) -> Customer | None:
    """Найти клиента по идентификатору."""
    for customer in customers:
        if customer.id == customer_id:
            return customer
    return None


def find_customer_by_phone(
    customers: list[Customer], phone: str
) -> Customer | None:
    """Найти клиента по точному совпадению телефона."""
    for customer in customers:
        if customer.phone == phone:
            return customer
    return None


def show_customers(customers: list[Customer]) -> None:
    """Вывести список клиентов."""
    if not customers:
        print("Клиентов пока нет")
        return
    for customer in customers:
        print(customer)
