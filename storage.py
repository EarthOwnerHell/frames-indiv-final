"""Сохранение и загрузка данных приложения в формате JSON."""

import json
import os


def load_json(filename: str) -> list[dict]:
    """Загрузить список данных из JSON-файла.

    Отсутствие файла или повреждённый JSON не прерывают программу:
    в этом случае возвращается пустой список.
    """
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print(f"Файл {filename} повреждён, данные не загружены")
        return []


def save_json(filename: str, data: list[dict]) -> None:
    """Сохранить список данных в JSON-файл.

    Каталог для файла создаётся автоматически, если ещё не существует.
    """
    directory = os.path.dirname(filename)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
