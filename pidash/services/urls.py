from django.urls import path

from pidash.services import views

app_name = "services"

urlpatterns = [
    path("", views.ServicesView.as_view(), name="page"),
    path("cards/", views.CardsPartial.as_view(), name="cards"),
    path("health/", views.HealthChip.as_view(), name="health"),
    path("<slug:service_id>/control/", views.control, name="control"),
    path("<slug:service_id>/run/", views.run, name="run"),
]
