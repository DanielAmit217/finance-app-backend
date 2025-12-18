from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authtoken.models import Token
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .serializers import (
    SignUpSerializer,
    SignInSerializer,
    UserSerializer,
    UserDetailSerializer,
    AccountSerializer,
    TransactionSerializer,
)
from .models import Account, Transaction


def home(request):
    return HttpResponse("<h1>hello ᓚᘏᗢ</h1>")


class SignUpView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Create token for the new user
            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {
                    "user": UserSerializer(user).data,
                    "token": token.key,
                    "message": "User created successfully",
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SignInView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SignInSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {
                    "user": UserSerializer(user).data,
                    "token": token.key,
                    "message": "Login successful",
                },
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AccountViewSet(ModelViewSet):
    """ViewSet for Account CRUD operations"""

    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return only accounts owned by current user"""
        return Account.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Auto-assign account to current user"""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["get"])
    def transactions(self, request, pk=None):
        """Get transactions for this account (GET /accounts/{id}/transactions/)"""
        account = self.get_object()
        transactions = account.transactions.filter(is_counter=False).order_by("-date")
        serializer = TransactionSerializer(
            transactions, many=True, context={"request": request}
        )
        return Response(serializer.data)


class TransactionViewSet(ModelViewSet):
    """ViewSet for Transaction CRUD operations with counter pattern support"""

    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Return only transactions owned by current user, exclude counters"""
        return Transaction.objects.filter(
            user=self.request.user, is_counter=False
        ).order_by("-date")

    def perform_create(self, serializer):
        """Auto-assign transaction to current user"""
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        """Update uses counter transaction pattern"""
        from .signals import create_counter_and_new_transaction

        # Get original transaction
        transaction = self.get_object()

        # Prevent editing counters
        if transaction.is_counter:
            raise ValueError("Cannot edit counter transactions")

        # Use counter pattern: create counter + new transaction
        counter_txn, new_txn = create_counter_and_new_transaction(
            transaction, serializer.validated_data
        )

        # Return new transaction (ViewSet will serialize it)
        # Note: The new_txn is created but we need to return it in response
        # We override to_representation to handle this
        self.instance = new_txn


class DashboardView(APIView):
    """Get user's dashboard with overall balance, accounts, income, and expenses"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Return user profile with balance information"""
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
