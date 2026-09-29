from django.urls import path

from . import views

urlpatterns = [
    path("", views.couriers, name="couriers"),
    path("<int:courier_id>/", views.courier_detail, name="courier_detail"),
]
