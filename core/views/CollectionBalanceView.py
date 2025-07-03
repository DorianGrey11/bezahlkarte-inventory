from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.timezone import now
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction as db_transaction
from django.contrib import messages

from core.models import Account, Transaction, Collection


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


class CollectionBalanceView(LoginRequiredMixin, View):
    def get(self, request, collection_id):
        collection = get_object_or_404(Collection, id=collection_id)
        accounts = Account.objects.filter(collection=collection)
        external_accounts = Account.objects.exclude(collection=collection)

        return render(request, 'balance.html', {
            'collection': collection,
            'accounts': accounts,
            'external_accounts': external_accounts,
            'balances': {acc.id: acc.balance for acc in accounts},
            'now': now(),
        })

    def post(self, request, collection_id):

        collection = get_object_or_404(Collection, id=collection_id)
        if "add_account" in request.POST:
            # Create new gift_card account
            Account.objects.create(
                collection=collection,
                name=request.POST.get(f"add_account_name"),
                type="gift_card",
            )
            messages.success(request, "Neue Gutscheinart wurde hinzugefügt.")
            return redirect('collection_balance', collection_id=collection.id)

        try:
            with db_transaction.atomic():
                accounts = Account.objects.filter(collection=collection)
                external_accounts = Account.objects.exclude(collection=collection)
                non_cash_accounts = accounts.exclude(type='cash')
                cash_account = accounts.get(type='cash')
                for acc in non_cash_accounts:
                    try:
                        desired_balance = float(request.POST.get(f"account_{acc.id}"))
                    except (TypeError, ValueError):
                        continue

                    delta = desired_balance - acc.balance

                    if delta != 0:
                        make_transaction(acc, cash_account, delta, request.user,
                                         request.POST.get(f"transaction_description"))

                desired_balance = float(request.POST.get(f"account_{cash_account.id}"))
                balance_mismatch = desired_balance - cash_account.balance
                if abs(balance_mismatch) > 0.01:
                    if request.POST.get('correction'):
                        correction_account = Account.objects.get(name="Fehlbetrag")
                        make_transaction(cash_account, correction_account, balance_mismatch, request.user,request.POST.get(f"transaction_description"))
                    else:
                        raise ValueError("Bilanz fehlerhaft.")

                if request.POST.get("enable_transfer"):
                    external_accounts_dict = {str(acc.id): acc for acc in external_accounts}
                    for acc in accounts:
                        transfer_target_id = request.POST.get(f"transfer_target_{acc.id}")
                        transfer_amount = request.POST.get(f"transfer_amount_{acc.id}")
                        if transfer_target_id and transfer_amount:
                            target_account = external_accounts_dict[transfer_target_id]
                            amount = float(transfer_amount)
                            make_transaction(acc, target_account, -amount, request.user,
                                             request.POST.get(f"transaction_description"))
        except ValueError as e:
            messages.error(request, e)
            return render(request, 'balance.html', {
                'collection': collection,
                'accounts': accounts,
                'external_accounts': external_accounts,
                'balances': {acc.id: acc.balance for acc in accounts},
                'balance_mismatch': balance_mismatch,
                'now': now(),
            })

        messages.success(request, "Bilanz erfolgreich aktualisiert.")
        return redirect('collection_balance', collection_id=collection_id)
