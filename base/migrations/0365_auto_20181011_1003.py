# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-10-11 10:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0364_auto_20181005_1215'),
    ]

    operations = [
        migrations.AlterField(
            model_name='educationgrouporganization',
            name='all_students',
            field=models.BooleanField(default=False, verbose_name='for_all_students'),
        ),
        migrations.AlterField(
            model_name='educationgrouporganization',
            name='diploma',
            field=models.CharField(choices=[('UNIQUE', 'UNIQUE'), ('SEPARATE', 'SEPARATE'), ('NOT_CONCERNED', 'NOT_CONCERNED')], default='NOT_CONCERNED', max_length=40, verbose_name='UCL Diploma'),
        ),
        migrations.AlterField(
            model_name='educationgrouporganization',
            name='enrollment_place',
            field=models.BooleanField(default=False, verbose_name='Reference institution'),
        ),
        migrations.AlterField(
            model_name='educationgrouporganization',
            name='is_producing_annexe',
            field=models.BooleanField(default=False, verbose_name='Producing annexe'),
        ),
        migrations.AlterField(
            model_name='educationgrouporganization',
            name='is_producing_cerfificate',
            field=models.BooleanField(default=False, verbose_name='Producing certificat'),
        ),
    ]
