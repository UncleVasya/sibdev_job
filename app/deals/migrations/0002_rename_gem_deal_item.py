# Generated by Django 4.2.3 on 2023-07-06 04:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('deals', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='deal',
            old_name='gem',
            new_name='item',
        ),
    ]
