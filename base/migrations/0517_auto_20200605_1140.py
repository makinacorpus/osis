# Generated by Django 2.2.10 on 2020-06-05 11:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0516_auto_20200602_1440'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='entitymanager',
            options={'verbose_name': 'Entity manager', 'verbose_name_plural': 'Entity managers'},
        ),
        migrations.RemoveField(
            model_name='entitymanager',
            name='uuid',
        ),
        migrations.AddField(
            model_name='entitymanager',
            name='with_child',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='entitymanager',
            name='entity',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.Entity'),
        ),
        migrations.AlterField(
            model_name='entitymanager',
            name='person',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='base.Person'),
        ),
    ]
