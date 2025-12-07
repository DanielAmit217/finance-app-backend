from django.db import models
import uuid
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from simple_history.models import HistoricalRecords
from djmoney.models.fields import MoneyField

# Create your models here.

#  הורשה ממודל USER
class User(AbstractUser): 
    username=None
    email=None 
    #מזהה מערכת פנימי KEY ייחודי
    app_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    #הגדרת טלפון כמזהה ייחודי וברירת מחדל להתחברות
    phone = models.CharField(max_length=10, unique=True)
    USERNAME_FIELD="phone"
    REQUIRED_FIELDS=[]
   # is_phone_verfied=
    preferred_currency = models.CharField(max_length=5, default="ILS")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    plan = models.CharField(
        max_length=20,
        choices=[
            ("free", "Free"),
            ("early_pro", "Early PRO"),
            ("pro", "PRO"),
        ],
        default="free"
    )
# צריך להסויף עוד מכשירים פינסים אחר כך
class Account(models.Model):
    
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name="accounts")
    
    ACCOUNT_TYPES = (
        ("bank", "Bank name"),
        ("credit_card", "Credit Card"),
    #    ("investment_account", "Investment Account"),
    #    ("pension_account", "Pension Account")
    )
    
    PROVIDERS = (
        ("pepper", "Pepper"),
        ("leumi", "Bank Leumi"),
        ("max", "Max Credit"),
        ("isracard", "Isracard"),
        ("cal", "CAL"),
        ("unknown", "Unknown Provider"))
    
    provider = models.CharField(
        max_length=30,
        choices=PROVIDERS,
        default="unknown")
    
   
    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPES,
    )
    
    initial_balance = MoneyField(
        max_digits=10, decimal_places=2, default_currency="ILS"
    )
    current_balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0)
    history = HistoricalRecords()
    last_synced = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)


   # לMVP מקבלים CSV של לאומי(ופפר) וכרטיסי MAX וישרכארט
class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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


