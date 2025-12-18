from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Transaction, Account


class SignUpSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, min_length=6, style={"input_type": "password"}
    )
    password_confirm = serializers.CharField(
        write_only=True, min_length=6, style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
        ]
        extra_kwargs = {
            "email": {"required": True},
            "first_name": {"required": False},
            "last_name": {"required": False},
        }

    def validate(self, data):
        if data["password"] != data["password_confirm"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})

        if User.objects.filter(username=data["username"]).exists():
            raise serializers.ValidationError(
                {"username": "This username is already taken."}
            )

        if User.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError(
                {"email": "This email is already registered."}
            )

        return data

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class SignInSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, data):
        user = authenticate(
            username=data.get("username"), password=data.get("password")
        )

        if user is None:
            raise serializers.ValidationError(
                {"detail": "Invalid username or password."}
            )

        data["user"] = user
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "date_joined"]
        read_only_fields = ["id", "date_joined"]


class UserDetailSerializer(serializers.ModelSerializer):
    """User serializer with overall balance calculated from all accounts and transactions"""

    overall_balance = serializers.SerializerMethodField()
    accounts = serializers.SerializerMethodField()
    total_income = serializers.SerializerMethodField()
    total_expenses = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "date_joined",
            "overall_balance",
            "total_income",
            "total_expenses",
            "accounts",
        ]
        read_only_fields = [
            "id",
            "date_joined",
            "overall_balance",
            "total_income",
            "total_expenses",
        ]

    def get_overall_balance(self, obj):
        """Sum balance across all user accounts"""
        from djmoney.money import Money

        total_balance = Money(0, "USD")

        for account in obj.account_set.all():
            total_balance += account.balance

        return {
            "amount": float(total_balance.amount),
            "currency": str(total_balance.currency),
            "formatted": f"{total_balance.currency} {total_balance.amount:,.2f}",
        }

    def get_total_income(self, obj):
        """Calculate total income across all transactions"""
        from django.db.models import Sum

        total = Transaction.objects.filter(
            user=obj, transaction_type=Transaction.INCOME
        ).aggregate(total=Sum("amount_amount", default=0))["total"]

        return {
            "amount": float(total),
            "currency": "USD",
            "formatted": f"USD {total:,.2f}",
        }

    def get_total_expenses(self, obj):
        """Calculate total expenses across all transactions"""
        from django.db.models import Sum

        total = Transaction.objects.filter(
            user=obj, transaction_type=Transaction.EXPENSE
        ).aggregate(total=Sum("amount_amount", default=0))["total"]

        return {
            "amount": float(total),
            "currency": "USD",
            "formatted": f"USD {total:,.2f}",
        }

    def get_accounts(self, obj):
        """Return all accounts with their balances"""
        accounts = obj.account_set.all()
        return AccountWithBalanceSerializer(accounts, many=True).data


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ["id", "name", "bank_name", "balance", "created_at"]
        read_only_fields = ["id", "created_at", "balance"]


class AccountWithBalanceSerializer(serializers.ModelSerializer):
    """Account serializer with current balance"""

    class Meta:
        model = Account
        fields = [
            "id",
            "name",
            "bank_name",
            "balance",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "balance"]


class TransactionSerializer(serializers.ModelSerializer):
    account_name = serializers.CharField(source="account.name", read_only=True)
    transaction_type_display = serializers.CharField(
        source="get_transaction_type_display", read_only=True
    )

    class Meta:
        model = Transaction
        fields = [
            "id",
            "description",
            "account",
            "account_name",
            "amount",
            "transaction_type",
            "transaction_type_display",
            "is_recurring",
            "date",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, data):
        # Ensure the account belongs to the user making the request
        request = self.context.get("request")
        if request and data.get("account"):
            if data["account"].user != request.user:
                raise serializers.ValidationError(
                    {"account": "This account does not belong to you."}
                )
        return data
