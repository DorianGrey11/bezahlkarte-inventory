from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.utils.timezone import now
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction as db_transaction
from django.contrib import messages
from guardian.shortcuts import get_objects_for_user

from core.models import Account, Collection
from core.views.utils import make_transaction


class TransferView(LoginRequiredMixin, View):
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
        external_accounts = Account.objects.exclude(collection=collection)

        return render(request, 'transfer.html', {
            'collection': collection,
            'accounts': accounts,
            'external_accounts': external_accounts,
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
            raise Http404

        try:
            with db_transaction.atomic():
                accounts = collection.accounts.all()
                external_accounts = Account.objects.exclude(collection=collection)
                external_accounts_dict = {str(acc.id): acc for acc in external_accounts}
                for acc in accounts:
                    transfer_target_id = request.POST.get(f"transfer_target_{acc.id}")
                    transfer_amount = request.POST.get(f"transfer_amount_{acc.id}")
                    transfer_number_of_gift_cards = request.POST.get(f"transfer_number_of_gift_cards_{acc.id}")
                    if transfer_target_id and (transfer_amount or transfer_number_of_gift_cards):
                        target_account = external_accounts_dict[transfer_target_id]
                        amount = float(transfer_amount) if transfer_amount else 0.0
                        number_of_gift_cards = int(
                            transfer_number_of_gift_cards) if transfer_number_of_gift_cards else 0
                        make_transaction(acc, target_account, -amount, -number_of_gift_cards, request.user,
                                         request.POST.get(f"transaction_description"))
                messages.success(request, "Transfer erfolgreich.")
        except Exception as e:
            messages.error(request, e)
        return redirect('transfer', collection_id=collection_id)
