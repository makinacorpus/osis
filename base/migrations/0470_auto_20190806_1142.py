# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2019-08-05 13:39
from __future__ import unicode_literals

from django.db import migrations, connection


def start_years(apps, schema_editor):
    education_group_model = apps.get_model('base', 'educationgroup')
    education_groups = education_group_model.objects.all()
    academic_year_model = apps.get_model('base', 'academicyear')
    academic_years = academic_year_model.objects.all().values('pk', 'year')
    for education_group in education_groups:
        academic_year_id = list(filter(lambda item: item['year'] == education_group.start_year, academic_years))
        if academic_year_id:
            education_group.new_start_year_id = academic_year_id[0]['pk']
            education_group.save()
        academic_year_id = list(filter(lambda item: item['year'] == education_group.end_year, academic_years))
        if academic_year_id:
            education_group.new_end_year_id = academic_year_id[0]['pk']
            education_group.save()


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0469_auto_20190806_1141'),
    ]

    operations = [
        migrations.RunPython(start_years, reverse_code=migrations.RunPython.noop),
    ]
