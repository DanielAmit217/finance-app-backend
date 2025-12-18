from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from simple_history.models import HistoricalRecords
from djmoney.models.fields import MoneyField
import os

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
    amount = MoneyField(max_digits=10, decimal_places=2, default_currency="ILS")
    transaction_type = models.CharField(
        max_length=2, choices=TRANSACTION_TYPE, default=EXPENSE
    )
    is_recurring = models.BooleanField(default=False)
    is_counter = models.BooleanField(
        default=False, help_text="True if this is a counter transaction (edit/delete)"
    )
    counter_transaction = models.OneToOneField(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="counter_for",
        help_text="Points to the original transaction this counters",
    )
    date = models.DateField()
    history = HistoricalRecords()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        type_display = self.get_transaction_type_display()
        counter_label = " (COUNTER)" if self.is_counter else ""
        return f"{self.amount} {type_display} on {self.date} (account: {self.account.name}){counter_label}"


class MonthlySummary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account = models.ForeignKey(
        "Account",
        on_delete=models.CASCADE,
        related_name="monthly_summaries",
        help_text="Account this summary belongs to",
        null=True,
        blank=True,
    )
    month = models.DateField(help_text="First day of the month")
    balance = MoneyField(
        max_digits=10,
        decimal_places=2,
        default_currency="ILS",
        help_text="Balance at end of this month",
        null=True,
        blank=True,
    )
    history = HistoricalRecords()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [("account", "month")]
        ordering = ["-month"]

    def __str__(self):
        return f"Summary for {self.month.strftime('%B %Y')} - Account: {self.account.name if self.account else 'N/A'} - Balance: {self.balance}"


class SourceFile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to="uploads/")
    account = models.ForeignKey("Account", on_delete=models.CASCADE)
    history = HistoricalRecords()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        filename = os.path.basename(self.file.name)
        return f"{filename} (Account: {self.account.name})"


class Account(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    bank_name = models.CharField(max_length=50, blank=True)
    balance = MoneyField(
        max_digits=10, decimal_places=2, default_currency="ILS", default=0
    )
    history = HistoricalRecords()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.name} - {self.user.username}"
