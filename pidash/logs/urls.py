from django.urls import path

from pidash.logs import views

app_name = "logs"

urlpatterns = [
    path("", views.LogsView.as_view(), name="page"),
    path("console/", views.ConsolePartial.as_view(), name="console"),
    path("<slug:service_id>/clear/", views.clear_log, name="clear"),
]
