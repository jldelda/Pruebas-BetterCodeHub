# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-27 02:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edx', '0006_auto_20171027_0205'),
    ]

    operations = [
        migrations.AlterField(
            model_name='useridmap',
            name='hash_id',
            field=models.CharField(max_length=40, primary_key=True, serialize=False),
        ),
    ]
