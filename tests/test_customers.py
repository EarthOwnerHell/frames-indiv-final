from models import Customer
from models.customers import (
    add_customer,
    find_customer,
    find_customer_by_id,
    find_customer_by_phone,
)


def test_customer_creation():
    customer = Customer(1, "Иван Петров", "+7 900 111-22-33")
    assert customer.id == 1
    assert customer.name == "Иван Петров"
    assert customer.phone == "+7 900 111-22-33"


def test_customer_str():
    customer = Customer(1, "Иван Петров", "+7 900 111-22-33")
    assert str(customer) == "#1 Иван Петров, +7 900 111-22-33"


def test_customer_from_data():
    data = {"id": 5, "name": "Анна Смирнова", "phone": "+7 900 555-55-55"}
    customer = Customer.from_data(data)
    assert isinstance(customer, Customer)
    assert customer.id == 5
    assert customer.name == "Анна Смирнова"


def test_add_customer_assigns_incremental_id():
    customers = []
    first = add_customer(customers, "Иван Петров", "+7 900 000-00-01")
    second = add_customer(customers, "Анна Смирнова", "+7 900 000-00-02")
    assert first.id == 1
    assert second.id == 2
    assert customers == [first, second]


def test_find_customer_by_name_or_phone():
    customers = []
    add_customer(customers, "Иван Петров", "+7 900 111-22-33")
    add_customer(customers, "Анна Смирнова", "+7 900 444-55-66")
    assert [c.name for c in find_customer(customers, "иван")] == [
        "Иван Петров"
    ]
    assert [c.name for c in find_customer(customers, "444")] == [
        "Анна Смирнова"
    ]


def test_find_customer_by_id_and_phone():
    customers = []
    customer = add_customer(customers, "Иван Петров", "+7 900 111-22-33")
    assert find_customer_by_id(customers, 1) is customer
    assert find_customer_by_id(customers, 99) is None
    assert find_customer_by_phone(customers, "+7 900 111-22-33") is customer
    assert find_customer_by_phone(customers, "+7 000") is None
