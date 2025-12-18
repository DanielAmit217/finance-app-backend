from django.shortcuts import render
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .serializers import (
    SignUpSerializer,
    SignInSerializer,
    UserSerializer,
    UserDetailSerializer,
    AccountSerializer,
    AccountWithBalanceSerializer,
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


class AccountListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get all accounts for the authenticated user"""
        accounts = Account.objects.filter(user=request.user)
        serializer = AccountSerializer(accounts, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new account for the authenticated user"""
        serializer = AccountSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AccountDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_account(self, account_id, user):
        """Helper to get account and check ownership"""
        try:
            account = Account.objects.get(id=account_id, user=user)
            return account
        except Account.DoesNotExist:
            return None

    def get(self, request, account_id):
        """Get a specific account"""
        account = self.get_account(account_id, request.user)
        if not account:
            return Response(
                {"detail": "Account not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = AccountSerializer(account)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, account_id):
        """Update an account"""
        account = self.get_account(account_id, request.user)
        if not account:
            return Response(
                {"detail": "Account not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = AccountSerializer(account, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, account_id):
        """Delete an account"""
        account = self.get_account(account_id, request.user)
        if not account:
            return Response(
                {"detail": "Account not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        account.delete()
        return Response(
            {"message": "Account deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )


class TransactionListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get all transactions for the authenticated user"""
        transactions = Transaction.objects.filter(user=request.user).order_by("-date")
        serializer = TransactionSerializer(
            transactions, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new transaction for the authenticated user"""
        serializer = TransactionSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TransactionDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_transaction(self, transaction_id, user):
        """Helper to get transaction and check ownership"""
        try:
            transaction = Transaction.objects.get(id=transaction_id, user=user)
            return transaction
        except Transaction.DoesNotExist:
            return None

    def get(self, request, transaction_id):
        """Get a specific transaction"""
        transaction = self.get_transaction(transaction_id, request.user)
        if not transaction:
            return Response(
                {"detail": "Transaction not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = TransactionSerializer(transaction, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, transaction_id):
        """Update a transaction"""
        transaction = self.get_transaction(transaction_id, request.user)
        if not transaction:
            return Response(
                {"detail": "Transaction not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = TransactionSerializer(
            transaction,
            data=request.data,
            partial=True,
            context={"request": request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, transaction_id):
        """Delete a transaction"""
        transaction = self.get_transaction(transaction_id, request.user)
        if not transaction:
            return Response(
                {"detail": "Transaction not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        transaction.delete()
        return Response(
            {"message": "Transaction deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )


class AccountTransactionsView(APIView):
    """Get all transactions for a specific account"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, account_id):
        """Get transactions for a specific account"""
        try:
            account = Account.objects.get(id=account_id, user=request.user)
        except Account.DoesNotExist:
            return Response(
                {"detail": "Account not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        transactions = account.transactions.all().order_by("-date")
        serializer = TransactionSerializer(
            transactions, many=True, context={"request": request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class DashboardView(APIView):
    """Get user's dashboard with overall balance, accounts, income, and expenses"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Return user profile with balance information"""
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
