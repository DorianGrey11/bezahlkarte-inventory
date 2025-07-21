from django.contrib import admin

from .models import Collection, Account, Transaction

from guardian.admin import GuardedModelAdmin
from guardian.shortcuts import get_objects_for_user


class CollectionAdmin(GuardedModelAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return get_objects_for_user(request.user, 'core.view_collection', klass=qs)


admin.site.register(Collection, CollectionAdmin)
admin.site.register(Account)
admin.site.register(Transaction)
