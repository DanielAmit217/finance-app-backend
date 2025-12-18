from django.db.models.signals import post_save, post_delete, pre_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Transaction, Account, MonthlySummary
from djmoney.money import Money
from datetime import date


def get_first_day_of_month(d):
    """Get the first day of the month for a given date"""
    return date(d.year, d.month, 1)


def get_month_balance(account, target_month):
    """
    Get the starting balance for a month (previous month's ending balance).
    
    Example: If target_month is March 2025, returns February 2025's ending balance.
    """
    from dateutil.relativedelta import relativedelta
    
    previous_month = target_month - relativedelta(months=1)
    
    try:
        summary = MonthlySummary.objects.get(account=account, month=previous_month)
        return summary.balance
    except MonthlySummary.DoesNotExist:
        return Money(0, account.balance.currency)


def calculate_balance_from_month(account, from_month_date):
    """
    Calculate account balance starting from a specific month.

    Flow:
    1. Get the balance at the start of the month (from previous month's summary)
    2. Add/subtract all transactions in this month (including counters!)
       - Counters are designed as opposite amounts, so they naturally cancel
       - Original +500, Counter -500 → net 0 (cancels the edit)
       - New +400 is added normally

    This is O(n) where n = transactions in current month (much faster than O(total transactions))
    """
    month_first_day = get_first_day_of_month(from_month_date)

    # Start with the balance from the previous month's summary
    balance = get_month_balance(account, month_first_day)

    # Get ALL transactions from this month onwards
    # IMPORTANT: Include counter transactions!
    # Counters are opposite amounts, so they naturally reverse edits
    current_transactions = account.transactions.filter(
        date__gte=month_first_day
    ).order_by("date", "created_at")

    # Add income, subtract expenses
    for txn in current_transactions:
        if txn.transaction_type == Transaction.INCOME:
            balance += txn.amount
        else:  # EXPENSE
            balance -= txn.amount

    return balance


@receiver(post_save, sender=Transaction)
def update_account_balance_on_transaction_save(sender, instance, created, **kwargs):
    """
    Update account balance when a transaction is created or updated.

    Strategy:
    1. Calculate balance from the monthly summary of that month
    2. Include all non-counter transactions up to the current time
    3. Update the account's balance field

    This avoids recalculating from 0 - we only sum transactions from the current month forward.
    """
    # Skip if this is a counter transaction (we don't process counters, they're just audit trail)
    if instance.is_counter:
        return

    account = instance.account

    # Get the balance starting from the transaction's month
    new_balance = calculate_balance_from_month(account, instance.date)

    # Update account balance
    account.balance = new_balance
    account.save(update_fields=["balance"])


@receiver(pre_delete, sender=Transaction)
def create_counter_transaction_on_delete(sender, instance, **kwargs):
    """
    Instead of deleting, create a counter transaction.

    This ensures:
    1. Complete audit trail - nothing is ever deleted
    2. Double-entry bookkeeping - every transaction has a counter
    3. Historical accuracy - we can see what happened

    Example:
    - Original: +$100 income on Jan 5
    - User deletes it
    - Counter created: -$100 expense on Jan 5 (marked as counter)
    - Original transaction is NOT deleted
    - Account balance reflects: +100 - 100 = 0
    """
    if instance.is_counter:
        # Don't create counter for a counter (prevent infinite loops)
        return

    # Create counter transaction
    counter_type = (
        Transaction.EXPENSE
        if instance.transaction_type == Transaction.INCOME
        else Transaction.INCOME
    )

    counter_txn = Transaction.objects.create(
        user=instance.user,
        account=instance.account,
        description=f"COUNTER: {instance.description}",
        amount=instance.amount,
        transaction_type=counter_type,  # Flip the type
        is_counter=True,
        counter_transaction=instance,
        date=instance.date,
        is_recurring=False,
    )

    # Signal will fire automatically for the new counter transaction


def create_counter_and_new_transaction(original_transaction, new_data):
    """
    Handle transaction edit by creating counter + new transaction.

    This is called manually from the update API endpoint.

    Example:
    - Original: +$100 income
    - Edit to: +$50 income
    - Creates counter: -$100 expense (marks as counter)
    - Creates new: +$50 income (with same description/date)
    """
    # 1. Create counter to negate original
    counter_type = (
        Transaction.EXPENSE
        if original_transaction.transaction_type == Transaction.INCOME
        else Transaction.INCOME
    )

    counter_txn = Transaction.objects.create(
        user=original_transaction.user,
        account=original_transaction.account,
        description=f"COUNTER: {original_transaction.description}",
        amount=original_transaction.amount,
        transaction_type=counter_type,
        is_counter=True,
        counter_transaction=original_transaction,
        date=original_transaction.date,
        is_recurring=False,
    )

    # 2. Create new transaction with updated data
    new_txn = Transaction.objects.create(
        user=original_transaction.user,
        account=original_transaction.account,
        description=new_data.get("description", original_transaction.description),
        amount=new_data.get("amount", original_transaction.amount),
        transaction_type=new_data.get(
            "transaction_type", original_transaction.transaction_type
        ),
        is_recurring=new_data.get("is_recurring", original_transaction.is_recurring),
        date=new_data.get("date", original_transaction.date),
        is_counter=False,
        counter_transaction=None,
    )

    return counter_txn, new_txn


def create_monthly_summary(account, month_date):
    """
    Create or update a monthly summary for an account.

    Calculates the ending balance for the month and stores it as an anchor.
    This allows future calculations to start from this point instead of month 0.

    Should be called:
    - At end of each month (via scheduled task)
    - Or when first transaction of next month is created
    """
    month_first = get_first_day_of_month(month_date)

    # Calculate balance from this month
    balance = calculate_balance_from_month(account, month_date)

    # Get or create the summary
    summary, created = MonthlySummary.objects.update_or_create(
        account=account,
        month=month_first,
        defaults={
            "user": account.user,
            "balance": balance,
        },
    )

    return summary
