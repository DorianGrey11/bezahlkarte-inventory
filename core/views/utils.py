from core.models import Transaction


def make_transaction(account, to, amount, number_of_gift_cards, user, description):
    Transaction.objects.create(
        account=account,
        to=to,
        amount=amount,
        new_balance=account.balance + amount,
        number_of_gift_cards=number_of_gift_cards,
        new_number_of_gift_cards=account.number_of_gift_cards + number_of_gift_cards,
        user=user,
        description=description
    )
    Transaction.objects.create(
        account=to,
        to=account,
        amount=-amount,
        new_balance=to.balance - amount,
        number_of_gift_cards=-number_of_gift_cards,
        new_number_of_gift_cards=to.number_of_gift_cards - number_of_gift_cards,
        user=user,
        description=description
    )
