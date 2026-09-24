from django.urls import path

from pidash.system import views

app_name = "system"

urlpatterns = [
    path("", views.SystemView.as_view(), name="page"),
    path("tiles/", views.TilesPartial.as_view(), name="tiles"),
    path("schedule/", views.ScheduleView.as_view(), name="schedule"),
    path("bulk/", views.bulk, name="bulk"),
    path("clear-logs/", views.clear_logs, name="clear_logs"),
    path("power/", views.power, name="power"),
]
