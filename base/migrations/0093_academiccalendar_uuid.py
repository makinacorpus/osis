# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-01-16 14:07
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0092_populate_academiccalendar_uuid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='academiccalendar',
            name='uuid',
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
