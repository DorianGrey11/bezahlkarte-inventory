# Generated by Django 5.2.3 on 2025-07-30 22:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='new_number_of_gift_cards',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='transaction',
            name='number_of_gift_cards',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='account',
            name='type',
            field=models.CharField(choices=[('cash', 'Bargeld'), ('gift_card', 'Geschenkkarte'), ('administrative', 'Administrativ')], max_length=20),
        ),
    ]
