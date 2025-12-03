from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords
from djmoney.models.fields import MoneyField

# Create your models here.


class Transaction(models.Model):
    INCOME = "in"
    EXPENSE = "ex"
    TRANSACTION_TYPE = [
        (INCOME, "Income"),
        (EXPENSE, "Expense"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.CharField(max_length=255, blank=True)
    account = models.ForeignKey(
        "Account", on_delete=models.CASCADE, related_name="transactions"
    )
    amount = MoneyField(max_digits=10, decimal_places=2, default_currency="USD")
    transaction_type = models.CharField(
        max_length=2, choices=TRANSACTION_TYPE, default=EXPENSE
    )
    is_recurring = models.BooleanField(default=False)
    date = models.DateField()
    history = HistoricalRecords()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)


class MonthlySummary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    month = models.DateField()
    # total_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    # total_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    history = HistoricalRecords()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)


class SourceFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to="uploads/")
    account = models.ForeignKey("Account", on_delete=models.CASCADE)
    history = HistoricalRecords()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)


class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    bank_name = models.CharField(max_length=50, blank=True)
    initial_balance = MoneyField(
        max_digits=10, decimal_places=2, default_currency="USD"
    )
    history = HistoricalRecords()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
