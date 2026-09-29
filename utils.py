"""Вспомогательные функции безопасного ввода данных с консоли."""


def input_nonempty(prompt: str) -> str:
    """Запросить у пользователя непустую строку."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Значение не может быть пустым, попробуйте снова")


def input_float(prompt: str) -> float:
    """Запросить у пользователя дробное число."""
    while True:
        raw_value = input(prompt).strip().replace(",", ".")
        try:
            return float(raw_value)
        except ValueError:
            print("Введите число, например 12.5")


def input_int(prompt: str) -> int:
    """Запросить у пользователя целое число."""
    while True:
        raw_value = input(prompt).strip()
        try:
            return int(raw_value)
        except ValueError:
            print("Введите целое число")


def input_yes_no(prompt: str) -> bool:
    """Запросить у пользователя ответ да/нет и вернуть bool."""
    while True:
        raw_value = input(prompt + " (да/нет): ").strip().lower()
        if raw_value in ("да", "yes", "y", "д"):
            return True
        if raw_value in ("нет", "no", "n", "н"):
            return False
        print("Ответьте 'да' или 'нет'")
