# Generated by Django 5.1.3 on 2024-11-22 10:10

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('invoice', '0009_alter_customer_email_alter_invoiceitem_price_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoiceitem',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=19, validators=[
                django.core.validators.MinValueValidator(-1000000),
                django.core.validators.MaxValueValidator(1000000)]),
        ),
    ]
