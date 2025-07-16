from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django_tables2 import tables

from ..models import Transaction


class TransactionTable(tables.Table):
    account = tables.Column(verbose_name="Konto", orderable=True)
    amount = tables.Column(verbose_name="Betrag", orderable=True)
    to = tables.Column(verbose_name="Von / An", orderable=True)
    new_balance = tables.Column(verbose_name="Neuer Kontostand", orderable=True)
    user = tables.Column(verbose_name="User", orderable=True)
    description = tables.Column(verbose_name="Beschreibung", orderable=True)
    created_at = tables.Column(verbose_name="Zeitpunkt (UTC)", orderable=True)

    class Meta:
        model = Transaction
        fields = ("account", "amount", "to", "new_balance", "user", "description", "created_at")


class TransactionListView(LoginRequiredMixin, TemplateView):
    template_name = "transaction_list.html"

    def get_context_data(self, **kwargs):
        filter_kwargs = {filter_query: filter_value for filter_query, filter_value in
                         [("account__collection__name__contains", self.request.GET.get("collection")),
                          ("account__name__contains", self.request.GET.get("account")),
                          ("description__contains", self.request.GET.get("description")),
                          ("user__username__contains", self.request.GET.get("user")),
                          ]
                         if filter_value is not None
                         }
        table_data = Transaction.objects.filter(**filter_kwargs)
        return {"transactions": TransactionTable(table_data, order_by=self.request.GET.get("sort"))}
