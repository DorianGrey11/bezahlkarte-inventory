from django.contrib.auth.mixins import LoginRequiredMixin
from django_tables2 import tables, SingleTableView

from ..models import Transaction


class TransactionTable(tables.Table):
    account = tables.Column(verbose_name="Konto")
    amount = tables.Column(verbose_name="Betrag")
    to = tables.Column(verbose_name="An")
    new_balance = tables.Column(verbose_name="Neuer Kontostand")
    user = tables.Column(verbose_name="User")
    description = tables.Column(verbose_name="Beschreibung")
    created_at = tables.Column(verbose_name="Zeitpunkt (UTC)")

    class Meta:
        model = Transaction
        template_name = "django_tables2/bootstrap.html"
        fields = ("account", "amount", "to", "new_balance", "user", "description", "created_at")


class TransactionListView(LoginRequiredMixin, SingleTableView):
    model = Transaction
    table_class = TransactionTable
    template_name = 'transaction_list.html'
    context_object_name = 'transactions'
