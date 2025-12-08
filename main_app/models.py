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
    is_phone_verfied=models.BooleanField(default=False)
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

class UserSettings(models.Model):
    
    user = models.OneToOneField(
       settings.AUTH_USER_MODEL,
       on_delete=models.CASCADE,
       related_name="settings")
    
    preferred_currency = models.CharField(max_length=5, default="ILS")
    notifications_enabled = models.BooleanField(default=True)
    
    notification_level = models.CharField(max_length=20, choices=[
        ("minimal", "Minimal"),
        ("standard", "Standard"),
        ("detailed", "Detailed")
    ], default="standard")
    
    knowledge_level = models.CharField(
    max_length=20,
    choices=[
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
    ], default="beginner")
    
    interaction_style = models.CharField(max_length=20, choices=[
        ("gentle", "Gentle"),
        ("balanced", "Balanced"),
        ("direct","Direct")], default="balanced")
    

    
    

# צריך להסויף עוד מכשירים פינסים אחר כך
class FinanicalAccounts(models.Model):
    
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,related_name="accounts")
    
    ACCOUNT_TYPES = (
        ("bank", "Bank name"),
        ("credit_card", "Credit Card"),
    #    ("investment_account", "Investment Account"),
    #    ("pension_account", "Pension Account")
    )
    
    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPES,
    )
    
    PROVIDERS = (
        ("pepper", "Pepper"),
        ("leumi", "Bank Leumi"),
        ("max", "Max Credit"),
        ("isracard", "Isracard"),
        ("unknown", "Unknown Provider"))
    
    provider = models.CharField(
        max_length=30,
        choices=PROVIDERS,
        default="unknown")
    
   
   
    
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
    updated_at = models.DateTimeField(auto_now=True)
    
    

class Category(models.Model):
    # שם הקטגוריה (לדוגמה: Food, Shopping, Transport)
    name = models.CharField(max_length=50, unique=True)

    # מילות מפתח לזיהוי אוטומטי (טקסט מופרד בפסיקים)
    keywords = models.TextField(
        blank=True,
        help_text="Comma-separated keywords: ארומה, פיצה, קפה"
    )

    # למידת התנהגות משתמש — קישורים לתיאורים שסווגו בעבר
    learned_patterns = models.JSONField(
        null=True,
        blank=True,
        help_text="System-learned patterns (auto-added when user categorizes manually)"
    )

    # קטגוריה של המשתמש או קטגוריה גלובלית של המערכת
    # user=None → קטגוריה ברירת מחדל
    # user=<User> → קטגוריה אישית
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="custom_categories"
    )

    # מוכנים ל-MCC — עדיין לא בשימוש
    #mcc_codes = models.JSONField(
    #   null=True,
    #    blank=True,
    #   help_text="MCC codes for future Open Banking integration")
    

    # צבע ואייקון — ל-UI העתידי
    #  color = models.CharField(max_length=10, blank=True, null=True)
    #  icon = models.CharField(max_length=50, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    
   # לMVP מקבלים CSV של לאומי(ופפר) וכרטיסי MAX וישרכארט
class Transaction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    account = models.ForeignKey(
        "Account", on_delete=models.CASCADE, related_name="transactions"
    )
    
    INCOME = "income"
    EXPENSE = "expense"
    # TRANSFER_OUT = "transfer_out"     
    # TRANSFER_IN = "transfer_in"       
    # REFUND = "refund"                 
    # FEE = "fee"                       
    # ATM_WITHDRAW = "atm_withdraw"     
    # DEPOSIT = "deposit"               
    
    TRANSACTION_TYPE = [
        (INCOME, "Income"),
        (EXPENSE, "Expense"),
        # (TRANSFER_OUT, "Transfer Out"),
        # (TRANSFER_IN, "Transfer In"),
        # (REFUND, "Refund"),
        # (FEE, "Fee"),
        # (ATM_WITHDRAW, "ATM Withdraw"),
        # (DEPOSIT, "Deposit"),
    ]
    
    transaction_type = models.CharField(
        max_length=2, choices=TRANSACTION_TYPE, default=EXPENSE
    )
   
    amount = MoneyField(max_digits=10, decimal_places=2, default_currency="ILS")
    
    date=models.DateField()
    
    description = models.CharField(max_length=255)
    
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions"
    )
    
     # מזהה ייחודי מה־CSV למניעת כפילויות
    source_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Unique ID per CSV row to prevent duplicates"
    )
    # אולי בתור מודל נפרד
    #is_recurring = models.BooleanField(default=False)
    
     # האם העסקה סווגה אוטומטית או שהמשתמש תיקן אותה ידנית
    AUTO = "auto"
    MANUAL = "manual"

    CLASSIFICATION_TYPES = [
        (AUTO, "Auto"),
        (MANUAL, "Manual"),
    ]

    classification_type = models.CharField(
        max_length=10,
        choices=CLASSIFICATION_TYPES,
        default=AUTO
    )
    # מצב בו המערכת לא מצליחה לסווג לקטגוריה
    is_uncategorized = models.BooleanField(default=False)
    
    # המערכת/AI מסמן אם העסקה חשודה (לדוגמה: שינוי סכום חד, חיוב כפול )
    is_flagged = models.BooleanField(default=False)
    #  אם סכום העסקה גדול משמעותית פי 2-3 ממוצע ההוצאות בקטגוריה
    is_exptional=models.BooleanField(default=False)
    # מוכן לעתיד: MCC יגיע כשהמערכת תשתמש ב-Open Banking
    #mcc = models.IntegerField(null=True, blank=True)

    
    
    history = HistoricalRecords()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.date} - {self.description} ({self.amount})"
    
class IncomeProfile(models.Model):
    

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


