from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Earnings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()


class Expenses(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    month = models.DateField()


class Income(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=100, decimal_places=2)
    is_recurring = models.BooleanField(default=False)
    date = models.DateField()


class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=100, decimal_places=2)
    is_recurring = models.BooleanField(default=False)
    date = models.DateField()
