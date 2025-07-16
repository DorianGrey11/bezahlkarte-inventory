from core.models import Transaction


def make_transaction(account, to, amount, user, description):
    Transaction.objects.create(
        account=account,
        to=to,
        amount=amount,
        new_balance=account.balance + amount,
        user=user,
        description=description
    )
    Transaction.objects.create(
        account=to,
        to=account,
        amount=-amount,
        new_balance=to.balance - amount,
        user=user,
        description=description
    )
