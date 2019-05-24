# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2019-05-17 08:31
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0452_auto_20190510_1525'),
    ]

    operations = [
        migrations.AlterField(
            model_name='validationrule',
            name='placeholder',
            field=models.CharField(blank=True, max_length=25, verbose_name='Placeholder'),
        ),
        migrations.AlterUniqueTogether(
            name='groupelementyear',
            unique_together=set([('parent', 'child_branch'), ('parent', 'child_leaf')]),
        ),
    ]
