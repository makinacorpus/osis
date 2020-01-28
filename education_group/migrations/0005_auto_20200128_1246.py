# Generated by Django 2.2.5 on 2020-01-28 12:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('education_group', '0004_groupyear_management_entity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groupyear',
            name='acronym',
            field=models.CharField(db_index=True, max_length=40, verbose_name='Acronym/Short title'),
        ),
        migrations.AlterField(
            model_name='groupyear',
            name='partial_acronym',
            field=models.CharField(db_index=True, max_length=15, null=True, verbose_name='code'),
        ),
    ]
