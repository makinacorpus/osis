# Generated by Django 2.2.10 on 2020-04-16 12:34

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0511_auto_20200416_1234'),
        ('education_group', '0006_centraladmissionmanager_centralmanager_facultymanager'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupyear',
            name='active',
            field=models.CharField(choices=[('ACTIVE', 'Active'), ('INACTIVE', 'Inactive'), ('RE_REGISTRATION', 'Reregistration')], default='ACTIVE', max_length=20, verbose_name='Status'),
        ),
        migrations.AddField(
            model_name='groupyear',
            name='main_teaching_campus',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='teaching_campus', to='base.Campus', verbose_name='Learning location'),
        ),
    ]