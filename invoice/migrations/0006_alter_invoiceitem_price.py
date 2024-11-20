# Generated by Django 5.1.3 on 2024-11-20 13:32

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoice', '0005_alter_invoice_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoiceitem',
            name='price',
            field=models.FloatField(validators=[django.core.validators.MinValueValidator(-1000000), django.core.validators.MaxValueValidator(1000000)]),
        ),
    ]
