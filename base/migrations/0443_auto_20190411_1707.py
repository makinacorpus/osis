# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-04-11 17:07
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0442_programmanager_is_main'),
    ]

    operations = [
        migrations.AlterField(
            model_name='programmanager',
            name='person',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.Person', verbose_name='person'),
        ),
    ]
