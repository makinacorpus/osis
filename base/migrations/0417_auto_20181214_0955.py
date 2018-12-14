# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-12-14 09:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0416_educationgrouptype_learning_unit_child_allowed'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='groupelementyear',
            name='minor_access',
        ),
        migrations.AddField(
            model_name='groupelementyear',
            name='access_condition',
            field=models.BooleanField(default=False, verbose_name='access condition'),
        ),
    ]