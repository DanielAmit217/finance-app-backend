from django.contrib import admin
from .models import Transaction, MonthlySummary, SourceFile, Account

# Register your models here.

admin.site.register(Transaction)
admin.site.register(MonthlySummary)
admin.site.register(SourceFile)
admin.site.register(Account)
