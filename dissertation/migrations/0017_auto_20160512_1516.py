# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2016-05-12 13:16
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dissertation', '0016_auto_20160512_1154'),
    ]

    operations = [
        migrations.RenameField(
            model_name='adviser',
            old_name='email_accept',
            new_name='available_at_office',
        ),
        migrations.RenameField(
            model_name='adviser',
            old_name='office_accept',
            new_name='available_by_email',
        ),
        migrations.RenameField(
            model_name='adviser',
            old_name='phone_accept',
            new_name='available_by_phone',
        ),
    ]
