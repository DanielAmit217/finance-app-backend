from django.urls import path
from . import views

urlpatterns = [
    # to be added routes
    path("", views.home, name="home")
]
