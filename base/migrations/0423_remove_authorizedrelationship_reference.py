# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2019-01-15 12:02
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0422_auto_20190114_0725'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='authorizedrelationship',
            name='reference',
        ),
    ]