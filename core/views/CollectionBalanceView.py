from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils.timezone import now
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction as db_transaction
from django.contrib import messages
from guardian.shortcuts import get_objects_for_user

from core.models import Account, Collection
from core.views.utils import make_transaction


class CollectionBalanceView(LoginRequiredMixin, View):
    def get(self, request, collection_id):
        try:
            collection = get_objects_for_user(
                request.user,
                'core.change_collection',
                klass=Collection.objects.prefetch_related('accounts')
            ).get(id=collection_id)
        except Collection.DoesNotExist:
            raise Http404
        accounts = collection.accounts.all()

        return render(request, 'balance.html', {
            'collection': collection,
            'accounts': accounts,
            'now': now(),
        })

    def post(self, request, collection_id):
        try:
            collection = get_objects_for_user(
                request.user,
                'core.change_collection',
                klass=Collection.objects.prefetch_related('accounts')
            ).get(id=collection_id)
        except Collection.DoesNotExist:
            raise PermissionDenied

        if "add_account" in request.POST:
            try:
                if not request.user.has_perm('core.add_account'):
                    raise PermissionDenied("Keine Berechtigung, neue Konten hinzuzufügen.")
                # Create new gift_card account
                Account.objects.create(
                    collection=collection,
                    name=request.POST.get(f"add_account_name").strip().lower(),
                    type="gift_card",
                )
                messages.success(request, "Neue Gutscheinart wurde hinzugefügt.")
            except Exception as e:
                messages.error(request, e)
            return redirect('collection_balance', collection_id=collection.id)

        try:
            with db_transaction.atomic():
                accounts = collection.accounts.all()
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
                        make_transaction(cash_account, correction_account, balance_mismatch, request.user,
                                         request.POST.get(f"transaction_description"))
                    else:
                        raise ValueError("Bilanz fehlerhaft.")

        except ValueError as e:
            messages.error(request, e)
            return render(request, 'balance.html', {
                'collection': collection,
                'accounts': accounts,
                'balance_mismatch': balance_mismatch,
                'now': now(),
            })

        messages.success(request, "Bilanz erfolgreich aktualisiert.")
        return redirect('collection_balance', collection_id=collection_id)
