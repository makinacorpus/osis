# -*- coding: utf-8 -*-
# Generated by Django 1.9 on 2017-03-16 12:32
from __future__ import unicode_literals

import uuid

import django.db.models.deletion
from django.db import migrations, models

from internship.models.cohort import Cohort
from internship.models.organization import Organization
from internship.models.period import Period


def create_the_first_cohort(apps, schema_editor):
    Cohort.objects.create(name='2016-2017',
                          description='Groupe 1',
                          free_internships_number=8,
                          publication_start_date="2017-03-27",
                          subscription_start_date="2017-03-01",
                          subscription_end_date="2017-03-20")


def assign_first_cohort_to_periods(apps, schema_editor):
    cohort = Cohort.objects.first()

    Period.objects.all().update(cohort=cohort)
    Organization.objects.all().update(cohort=cohort)


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0098_auto_20170306_0953'),
        ('internship', '0034_internshipenrollment_internship_choice'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cohort',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True, null=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('free_internships_number', models.IntegerField()),
                ('publication_start_date', models.DateField()),
                ('subscription_start_date', models.DateField()),
                ('subscription_end_date', models.DateField()),
            ],
        ),
        migrations.AddField(
            model_name='organization',
            name='cohort',
            field=models.ForeignKey(null=True, default=None, on_delete=django.db.models.deletion.CASCADE, to='internship.Cohort'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='period',
            name='cohort',
            field=models.ForeignKey(null=True, default=None, on_delete=django.db.models.deletion.CASCADE,
                                    to='internship.Cohort'),
            preserve_default=False,
        ),
        migrations.RunPython(create_the_first_cohort),
        migrations.RunPython(assign_first_cohort_to_periods),
        migrations.RunSQL(
            "ALTER TABLE internship_period ALTER COLUMN cohort_id SET NOT NULL",
            reverse_sql="ALTER TABLE internship_period ALTER COLUMN cohort_id DROP NOT NULL"
        ),
        migrations.RunSQL(
            "ALTER TABLE internship_organization ALTER COLUMN cohort_id SET NOT NULL",
            reverse_sql="ALTER TABLE internship_organization ALTER COLUMN cohort_id DROP NOT NULL"
        ),
    ]
