"""Корневая маршрутизация: распределение адресов по приложениям."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("homepage.urls")),
    path("orders/", include("orders.urls")),
    path("couriers/", include("couriers.urls")),
]
