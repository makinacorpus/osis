# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-11-20 09:46
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0396_auto_20181119_1217'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='prerequisite',
            name='prerequisite',
        ),
    ]
