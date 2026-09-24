from django.urls import path

from pidash.channels import views

app_name = "channels"

urlpatterns = [
    path("", views.ChannelsView.as_view(), name="page"),
    path("<slug:service_id>/add/", views.add, name="add"),
    path("<slug:service_id>/remove/", views.remove, name="remove"),
]
