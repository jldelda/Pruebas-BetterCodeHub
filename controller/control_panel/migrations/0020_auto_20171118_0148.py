# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-18 06:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('control_panel', '0019_auto_20171114_2123'),
    ]

    operations = [
        migrations.AlterField(
            model_name='activityindex',
            name='max_inactivity_days',
            field=models.IntegerField(default=100, help_text='No recorded activity or enrolled less than this number of days'),
        ),
        migrations.AlterField(
            model_name='activityindex',
            name='min_inactivity_days',
            field=models.IntegerField(default=0, help_text='No recorded activity or enrolled greater than this number of days'),
        ),
        migrations.AlterField(
            model_name='activityindex',
            name='participant',
            field=models.BooleanField(default=False, help_text='Users with course activity'),
        ),
        migrations.AlterField(
            model_name='course',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
    ]
