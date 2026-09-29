"""Вспомогательные функции безопасного ввода данных с консоли."""

import math


def input_nonempty(prompt: str) -> str:
    """Запросить у пользователя непустую строку."""
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Значение не может быть пустым, попробуйте снова")


def input_float(prompt: str, min_value: float = 0.0) -> float:
    """Запросить у пользователя дробное число не меньше min_value."""
    while True:
        raw_value = input(prompt).strip().replace(",", ".")
        try:
            value = float(raw_value)
            if not math.isfinite(value):
                raise ValueError(raw_value)
        except ValueError:
            print("Введите число, например 12.5")
            continue
        if value < min_value:
            print(f"Значение не может быть меньше {min_value}")
            continue
        return value


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
