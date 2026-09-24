from django.contrib.auth.views import LogoutView
from django.urls import path

from pidash.core import views

app_name = "core"

urlpatterns = [
    path("", views.OverviewView.as_view(), name="overview"),
    path("sign-in/", views.SignInView.as_view(), name="login"),
    path("sign-out/", LogoutView.as_view(), name="logout"),
    path("healthz", views.healthz, name="healthz"),
]
