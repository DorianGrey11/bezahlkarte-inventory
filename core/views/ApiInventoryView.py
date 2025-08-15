from django.views import View
from django.http import JsonResponse

from core.models import Collection


class ApiInventoryView(View):
    def get(self, request):
        collections = Collection.objects.prefetch_related('accounts').filter(show_in_api=True)
        inventory = {
            collection.name: {
                account.name: {
                    "amount": account.number_of_gift_cards,
                    "total_value": account.balance
                } for account in collection.accounts.filter(type="gift_card") if account.balance > 0
            } for collection in collections
        }
        return JsonResponse(inventory)
