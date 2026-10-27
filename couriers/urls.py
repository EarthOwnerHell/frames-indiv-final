from django.urls import path

from . import views

app_name = "couriers"

urlpatterns = [
    path("", views.couriers, name="couriers"),
    path("available/", views.available, name="available"),
    path("<int:courier_id>/", views.courier_detail, name="courier_detail"),
]
