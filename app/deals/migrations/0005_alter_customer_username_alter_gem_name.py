# Generated by Django 4.2.3 on 2023-07-07 13:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deals', '0004_customer_gems'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='username',
            field=models.CharField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='gem',
            name='name',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
