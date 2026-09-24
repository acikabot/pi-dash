from django.urls import path

from pidash.recipients import views

app_name = "recipients"

urlpatterns = [
    path("", views.RecipientsView.as_view(), name="page"),
    path("<slug:service_id>/save/", views.save, name="save"),
]
