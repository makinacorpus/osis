# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-11-23 08:18
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dissertation', '0026_remove_propositiondissertation_offer_proposition'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dissertationrole',
            name='status',
            field=models.CharField(choices=[('PROMOTEUR', 'PROMOTEUR'), ('CO_PROMOTEUR', 'CO_PROMOTEUR'), ('READER', 'READER'), ('ACCOMPANIST', 'ACCOMPANIST'), ('INTERNSHIP', 'INTERNSHIP'), ('PRESIDENT', 'PRESIDENT')], max_length=12),
        ),
        migrations.AlterField(
            model_name='propositionrole',
            name='status',
            field=models.CharField(choices=[('PROMOTEUR', 'PROMOTEUR'), ('CO_PROMOTEUR', 'CO_PROMOTEUR'), ('READER', 'READER'), ('ACCOMPANIST', 'ACCOMPANIST'), ('INTERNSHIP', 'INTERNSHIP'), ('PRESIDENT', 'PRESIDENT')], default='PROMOTEUR', max_length=12),
        ),
    ]
