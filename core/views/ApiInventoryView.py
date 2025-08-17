from django.db.models import Max
from django.views import View
from django.http import JsonResponse

from core.models import Collection


class ApiInventoryView(View):
    def get(self, request):
        collections = (Collection.objects.prefetch_related('accounts')
                       .filter(show_in_api=True)
                       .annotate(updated_at=Max('accounts__transactions__created_at')))
        inventory = {
            collection.name: {
                "gift_cards": {
                    account.name: {
                        "amount": account.number_of_gift_cards,
                        "total_value": account.balance
                    } for account in collection.accounts.filter(type="gift_card") if account.balance > 0
                },
                "updated_at": collection.updated_at,
            } for collection in collections
        }
        response = JsonResponse(inventory)
        response['Access-Control-Allow-Origin'] = '*'
        return response
