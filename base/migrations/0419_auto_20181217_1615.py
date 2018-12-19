# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2018-12-17 16:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0418_remove_hops_uuid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='educationgrouptype',
            name='name',
            field=models.CharField(choices=[('AGGREGATION', 'Aggregation'), ('CERTIFICATE_OF_PARTICIPATION', 'Certificate of participation'), ('CERTIFICATE_OF_SUCCESS', 'Certificate of success'), ('CERTIFICATE_OF_HOLDING_CREDITS', 'Certificate of holding credits'), ('BACHELOR', 'Bachelor'), ('CERTIFICATE', 'Certificate'), ('CAPAES', 'CAPAES'), ('RESEARCH_CERTIFICATE', 'Research certificate'), ('UNIVERSITY_FIRST_CYCLE_CERTIFICATE', 'University first cycle certificate'), ('UNIVERSITY_SECOND_CYCLE_CERTIFICATE', 'University second cycle certificate'), ('ACCESS_CONTEST', 'Access contest'), ('LANGUAGE_CLASS', 'Language classes'), ('ISOLATED_CLASS', 'Isolated classes'), ('PHD', 'Ph.D'), ('FORMATION_PHD', 'Formation PhD'), ('JUNIOR_YEAR', 'Junior year'), ('PGRM_MASTER_120', 'Program master 120'), ('MASTER_MA_120', 'Master MA 120'), ('MASTER_MD_120', 'Master MD 120'), ('MASTER_MS_120', 'Master MS 120'), ('PGRM_MASTER_180_240', 'Program master 180-240'), ('MASTER_MA_180_240', 'Master MA 180-240'), ('MASTER_MD_180_240', 'Master MD 180-240'), ('MASTER_MS_180_240', 'Master MS 180-240'), ('MASTER_M1', 'Master in 60 credits'), ('MASTER_MC', 'Master of specialist'), ('INTERNSHIP', 'Internship'), ('DEEPENING', 'Deepening'), ('SOCIETY_MINOR', 'Society minor'), ('ACCESS_MINOR', 'Access minor'), ('OPEN_MINOR', 'Open minor'), ('DISCIPLINARY_COMPLEMENT_MINOR', 'Disciplinary complement minor'), ('FSA_SPECIALITY', 'FSA speciality'), ('OPTION', 'Option'), ('MOBILITY_PARTNERSHIP', 'Mobility partnership'), ('COMMON_CORE', 'Common core'), ('MINOR_LIST_CHOICE', 'Minor list choice'), ('MAJOR_LIST_CHOICE', 'Major list choice'), ('OPTION_LIST_CHOICE', 'Option list choice'), ('FINALITY_120_LIST_CHOICE', 'Finality 120 list choice'), ('FINALITY_180_LIST_CHOICE', 'Finality 180 list choice'), ('MOBILITY_PARTNERSHIP_LIST_CHOICE', 'Mobility partnership list choice'), ('COMPLEMENTARY_MODULE', 'Complementary module'), ('SUB_GROUP', 'Sub group')], max_length=255, unique=True, verbose_name='Type of training'),
        ),
    ]