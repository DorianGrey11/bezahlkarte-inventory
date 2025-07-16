from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.timezone import now
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction as db_transaction
from django.contrib import messages

from core.models import Account, Collection
from core.views.utils import make_transaction


class TransferView(LoginRequiredMixin, View):
    def get(self, request, collection_id):
        collection = get_object_or_404(Collection, id=collection_id)
        accounts = Account.objects.filter(collection=collection)
        external_accounts = Account.objects.exclude(collection=collection)

        return render(request, 'transfer.html', {
            'collection': collection,
            'accounts': accounts,
            'external_accounts': external_accounts,
            'now': now(),
        })

    def post(self, request, collection_id):
        collection = get_object_or_404(Collection, id=collection_id)
        try:
            with db_transaction.atomic():
                accounts = Account.objects.filter(collection=collection)
                external_accounts = Account.objects.exclude(collection=collection)
                external_accounts_dict = {str(acc.id): acc for acc in external_accounts}
                for acc in accounts:
                    transfer_target_id = request.POST.get(f"transfer_target_{acc.id}")
                    transfer_amount = request.POST.get(f"transfer_amount_{acc.id}")
                    if transfer_target_id and transfer_amount:
                        target_account = external_accounts_dict[transfer_target_id]
                        amount = float(transfer_amount)
                        make_transaction(acc, target_account, -amount, request.user,
                                         request.POST.get(f"transaction_description"))
                messages.success(request, "Transfer erfolgreich.")
        except Exception as e:
            messages.error(request, e)
        return redirect('transfer', collection_id=collection_id)
