# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-13 00:12
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('edx', '0009_auto_20171029_0008'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentCourseaccessrole',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_id', models.CharField(db_column='course_id', db_index=True, max_length=255)),
                ('role', models.CharField(max_length=255)),
                ('user_id', models.ForeignKey(db_column='user_id', on_delete=django.db.models.deletion.CASCADE, to='edx.AuthUser')),
            ],
            options={
                'db_table': 'student_courseaccessrole',
            },
        ),
    ]