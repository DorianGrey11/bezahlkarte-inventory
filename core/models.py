import uuid
from datetime import datetime, timezone

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Collection(models.Model):
    name = models.CharField(max_length=100)
    show_in_api = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Account(models.Model):
    TYPES = {
        'cash': 'Bargeld',
        'gift_card': 'Geschenkkarte',
        'administrative': 'Administrativ',
    }
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='accounts')
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=20, choices=TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return  f"{self.name} ({self.collection.name})"

    @property
    def balance(self):
        """Returns the most recent new_balance recorded for this account"""
        latest_transaction = self.transactions.order_by('-created_at').first()
        return latest_transaction.new_balance if latest_transaction else 0.0

    @property
    def number_of_gift_cards(self):
        """Returns the most recent new_number_of_gift_cards recorded for this account"""
        if self.type == "cash":
            return 0
        latest_transaction = self.transactions.order_by('-created_at').first()
        return latest_transaction.new_number_of_gift_cards if latest_transaction else 0

    def transfer(self, amount, to_account, description='', now=datetime.now(timezone.utc)):
        """
        Create a transaction transferring `amount` from this account to `to_account`.
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if self.balance < amount:
            raise ValueError("Insufficient balance")

        transaction = Transaction.objects.create(
            account=self,
            to=to_account,
            amount=-amount,
            description=description,
            new_balance=self.balance - amount,
            created_at=now,
            user=User.objects.get(username='system'),
        )
        Transaction.objects.create(
            account=to_account,
            to=self,
            amount=amount,
            description=description,
            new_balance=to_account.balance + amount,
            created_at=now,
            user=User.objects.get(username='system'),
        )
        return transaction

class Transaction(models.Model):
    account = models.ForeignKey(Account, on_delete=models.DO_NOTHING, related_name='transactions')
    to = models.ForeignKey(Account, on_delete=models.DO_NOTHING, related_name='incoming_transactions')
    amount = models.FloatField()
    number_of_gift_cards = models.IntegerField()
    description = models.TextField(blank=True)
    new_balance = models.FloatField()
    new_number_of_gift_cards = models.IntegerField()
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.account.name} → {self.to.name}: {self.amount:.2f} ({self.description})"
