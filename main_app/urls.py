from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r"accounts", views.AccountViewSet, basename="account")
router.register(r"transactions", views.TransactionViewSet, basename="transaction")

urlpatterns = [
    # Home endpoint
    path("", views.home, name="home"),
    # Authentication endpoints
    path("auth/sign-up/", views.SignUpView.as_view(), name="sign_up"),
    path("auth/sign-in/", views.SignInView.as_view(), name="sign_in"),
    # Dashboard endpoint
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    # Router-generated endpoints (accounts + transactions)
    path("", include(router.urls)),
]
