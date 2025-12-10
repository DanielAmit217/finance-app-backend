from django.urls import path
from . import views

urlpatterns = [
    # Home endpoint
    path("", views.home, name="home"),
    # Authentication endpoints
    path("auth/sign-up/", views.SignUpView.as_view(), name="sign_up"),
    path("auth/sign-in/", views.SignInView.as_view(), name="sign_in"),
    # Account endpoints
    path(
        "accounts/", views.AccountListCreateView.as_view(), name="account_list_create"
    ),
    path(
        "accounts/<int:account_id>/",
        views.AccountDetailView.as_view(),
        name="account_detail",
    ),
    path(
        "accounts/<int:account_id>/transactions/",
        views.AccountTransactionsView.as_view(),
        name="account_transactions",
    ),
    # Transaction endpoints
    path(
        "transactions/",
        views.TransactionListCreateView.as_view(),
        name="transaction_list_create",
    ),
    path(
        "transactions/<int:transaction_id>/",
        views.TransactionDetailView.as_view(),
        name="transaction_detail",
    ),
]
