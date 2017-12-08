# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-25 03:36
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('edx', '0003_auto_20171025_0331'),
    ]

    operations = [
        migrations.AlterField(
            model_name='authuserprofile',
            name='user_id',
            field=models.ForeignKey(db_column='user_id', on_delete=django.db.models.deletion.CASCADE, to='edx.AuthUser'),
        ),
        migrations.AlterField(
            model_name='studentcourseenrollment',
            name='user_id',
            field=models.ForeignKey(db_column='user_id', on_delete=django.db.models.deletion.CASCADE, to='edx.AuthUser'),
        ),
        migrations.AlterField(
            model_name='useridmap',
            name='id',
            field=models.ForeignKey(db_column='id', on_delete=django.db.models.deletion.CASCADE, related_name='+', to='edx.AuthUser'),
        ),
        migrations.AlterField(
            model_name='useridmap',
            name='username',
            field=models.ForeignKey(db_column='username', on_delete=django.db.models.deletion.CASCADE, related_name='+', to='edx.AuthUser', to_field='username'),
        ),
    ]
