# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-10-24 14:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0376_auto_20181022_1510'),
    ]

    operations = [
        migrations.AlterField(
            model_name='educationgroupyear',
            name='partial_acronym',
            field=models.CharField(db_index=True, max_length=15, null=True, verbose_name='code'),
        ),
    ]