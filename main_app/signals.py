from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Transaction, Account
from djmoney.money import Money


@receiver(post_save, sender=Transaction)
def update_account_balance_on_transaction_save(sender, instance, created, **kwargs):
    """
    Update the account balance whenever a transaction is created or updated.
    
    This signal handler:
    - Gets the associated account
    - Recalculates the total balance based on ALL transactions for that account
    - Saves the new balance to the account
    
    Why this approach:
    - Ensures accuracy: If a transaction is edited, balance updates automatically
    - Maintains history: simple_history tracks every balance change
    - O(1) reads: Balance is now a stored field, not calculated on every read
    """
    account = instance.account
    
    # Get the old previous transaction for this transaction if it was updated
    # We need to recalculate from scratch to handle all cases
    all_transactions = account.transactions.all()
    
    # Start with 0 balance
    new_balance = Money(0, account.balance.currency)
    
    # Add all income transactions
    for txn in all_transactions.filter(transaction_type=Transaction.INCOME):
        new_balance += txn.amount
    
    # Subtract all expense transactions
    for txn in all_transactions.filter(transaction_type=Transaction.EXPENSE):
        new_balance -= txn.amount
    
    # Update the account balance and save
    account.balance = new_balance
    account.save()


@receiver(post_delete, sender=Transaction)
def update_account_balance_on_transaction_delete(sender, instance, **kwargs):
    """
    Update the account balance whenever a transaction is deleted.
    
    Same logic as the save signal, but triggered on deletion.
    """
    account = instance.account
    
    # Recalculate balance from remaining transactions
    all_transactions = account.transactions.all()
    new_balance = Money(0, account.balance.currency)
    
    # Add all income transactions
    for txn in all_transactions.filter(transaction_type=Transaction.INCOME):
        new_balance += txn.amount
    
    # Subtract all expense transactions
    for txn in all_transactions.filter(transaction_type=Transaction.EXPENSE):
        new_balance -= txn.amount
    
    # Update the account balance and save
    account.balance = new_balance
    account.save()
