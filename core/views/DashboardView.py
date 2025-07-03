from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from .TransactionListView import TransactionTable
from ..models import Collection, Transaction, Account


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def post(self, request):
        if "add_collection" in request.POST:
            with transaction.atomic():
                collection = Collection.objects.create(
                    name=request.POST.get(f"add_collection_name"),
                )
                Account.objects.create(collection=collection, name="Bargeld", type="cash")
            messages.success(request, "Neues Konto/Kasse hinzugefügt.")
            return redirect('dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        collections = Collection.objects.prefetch_related('accounts').order_by('name')
        try:
            selected_collection_id = self.request.GET.get("collection")
            collections = [collections.get(id=selected_collection_id)]
            account_names = list(Account.objects.filter(collection=selected_collection_id).values_list("name", flat=True).distinct())
        except Collection.DoesNotExist:
            collections = collections
            account_names = list(Account.objects.order_by("type").reverse().values_list("name", flat=True).distinct())

        table = []
        for collection in collections:
            accounts_in_collection = {acc.name: acc for acc in collection.accounts.all()}
            row = {
                'collection': collection,
                'balances': [
                    (name, accounts_in_collection.get(name).balance if name in accounts_in_collection else None)
                    for name in account_names],
            }
            table.append(row)

        context.update({
            'account_headers': account_names,
            'collections': table,
            'transaction_table': TransactionTable(Transaction.objects.filter(account__collection__in=collections))
        })
        return context
