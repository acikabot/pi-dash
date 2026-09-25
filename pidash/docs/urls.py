from django.urls import path

from pidash.docs import views

app_name = "docs"

urlpatterns = [
    path("", views.DocIndexView.as_view(), name="index"),
    path("<slug:slug>/", views.DocPageView.as_view(), name="page"),
]
