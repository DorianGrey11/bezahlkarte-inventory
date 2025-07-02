from django.contrib import admin

from .models import Collection, Account, Transaction

admin.site.register(Collection)
admin.site.register(Account)
admin.site.register(Transaction)