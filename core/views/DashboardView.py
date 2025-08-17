from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from guardian.shortcuts import get_objects_for_user

from .TransactionListView import TransactionTable
from ..models import Collection, Transaction, Account

NUMBER_OF_TRANSACTIONS_LISTED = 12
STANDARD_GIFT_CARDS = ["aldi", "dm", "kaufland", "lidl", "rewe"]


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def post(self, request):
        try:
            if not self.request.user.has_perm('core.add_collection'):
                raise PermissionDenied("Keine Berechtigung eine neues Konto/Kasse zu erstellen.")
            with transaction.atomic():
                collection = Collection.objects.create(
                    name=request.POST.get(f"add_collection_name"),
                    show_in_api=request.POST.get(f"add_collection_show_in_api") == "on",
                )
                Account.objects.create(collection=collection, name="Bargeld", type="cash")
                if request.POST.get(f"add_collection_standard_gift_cards"):
                    for name in STANDARD_GIFT_CARDS:
                        Account.objects.create(collection=collection, name=name, type="gift_card")

            messages.success(request, "Neues Konto/Kasse hinzugefügt.")
        except Exception as e:
            messages.error(request, e)
        return redirect('dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        collections = get_objects_for_user(
            self.request.user,
            'core.view_collection',
            klass=Collection.objects.prefetch_related('accounts')
        ).order_by('name')
        try:
            selected_collection_id = self.request.GET.get("collection")
            collections = [collections.get(id=selected_collection_id)]
        except Collection.DoesNotExist:
            pass
        account_names = list(
            Account.objects.filter(collection__in=collections).order_by("-type", "name").values_list("name",
                                                                                                     flat=True).distinct())

        rows = []
        account_sums = [0 for _ in account_names]
        account_gift_cards = [0 for _ in account_names]
        for collection in collections:
            accounts_in_collection = {acc.name: acc for acc in collection.accounts.all()}
            row = {
                'collection': collection,
                'balances': [
                    (name,
                     accounts_in_collection.get(name).balance if name in accounts_in_collection else None,
                     accounts_in_collection.get(name).number_of_gift_cards if name in accounts_in_collection else None
                     )
                    for name in account_names
                ],
            }
            rows.append(row)

            for idx, balance in enumerate(row["balances"]):
                if balance[1] is not None:
                    account_sums[idx] += balance[1]
                if balance[2] is not None:
                    account_gift_cards[idx] += balance[2]

        context.update({
            'account_headers': account_names,
            'account_sums': zip(account_sums, account_gift_cards),
            'rows': rows,
            'transaction_table': TransactionTable(
                Transaction
                .objects
                .filter(account__collection__in=collections)
                .order_by("-created_at")[:NUMBER_OF_TRANSACTIONS_LISTED:1],
                order_by=self.request.GET.get("sort"))
            if self.request.user.has_perm('core.view_transaction') else None,
        })
        return context
