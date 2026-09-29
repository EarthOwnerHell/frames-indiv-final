from django.http import HttpRequest, HttpResponse

BOOTSTRAP_CSS = (
    "https://cdn.jsdelivr.net/npm/bootstrap@5.3.3"
    "/dist/css/bootstrap.min.css"
)


def page(title: str, content: str) -> str:
    """Собрать HTML-документ с общим каркасом: Bootstrap и навигация.

    Используется всеми приложениями проекта. Данные, попадающие
    в content, должны быть заранее экранированы через escape().
    """
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <link rel="stylesheet" href="{BOOTSTRAP_CSS}">
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand bg-dark mb-4" data-bs-theme="dark">
        <div class="container">
            <a class="navbar-brand" href="/">Доставка</a>
            <div class="navbar-nav">
                <a class="nav-link" href="/orders/">Заказы</a>
                <a class="nav-link" href="/couriers/">Курьеры</a>
            </div>
        </div>
    </nav>
    <main class="container pb-5">{content}</main>
</body>
</html>"""


def index(request: HttpRequest) -> HttpResponse:
    """Главная страница: описание сервиса и навигация по разделам."""
    content = """
    <h1 class="display-5">Сервис доставки заказов</h1>
    <p class="lead">
        Приём заказов, расчёт стоимости и срока доставки,
        назначение курьера и отслеживание статуса.
    </p>
    <p>Основные разделы:</p>
    <a href="/orders/" class="btn btn-primary me-2">Заказы</a>
    <a href="/couriers/" class="btn btn-secondary">Курьеры</a>
    """
    return HttpResponse(page("Сервис доставки заказов", content))
