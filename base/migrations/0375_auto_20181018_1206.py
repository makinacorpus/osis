# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-10-18 12:06
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0374_auto_20181018_0946'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='person',
            options={'permissions': (('is_administrator', 'Is administrator'), ('is_institution_administrator', 'Is institution administrator '), ('can_edit_education_group_administrative_data', 'Can edit education group administrative data'), ('can_manage_charge_repartition', 'Can manage charge repartition'))},
        ),
    ]