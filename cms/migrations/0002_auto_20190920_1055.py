# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2019-09-20 10:55
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cms', '0001_initial_squashed_0012_auto_20180807_1229'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='translatedtextlabel',
            unique_together=set([('language', 'text_label')]),
        ),
    ]
