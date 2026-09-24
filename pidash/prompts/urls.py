from django.urls import path

from pidash.prompts import views

app_name = "prompts"

urlpatterns = [
    path("", views.PromptsView.as_view(), name="page"),
    path("<slug:service_id>/<slug:prompt_id>/save/", views.save, name="save"),
    path("<slug:service_id>/<slug:prompt_id>/reset/", views.reset, name="reset"),
]
