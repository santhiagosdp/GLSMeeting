# Generated by Django 2.2.6 on 2019-10-08 01:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gls', '0004_auto_20190922_1209'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='workspace',
            name='created',
        ),
        migrations.RemoveField(
            model_name='workspace',
            name='modificacao',
        ),
    ]
