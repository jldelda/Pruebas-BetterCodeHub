# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-25 01:44
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('edx', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthUserprofile',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(db_index=True, max_length=255L)),
                ('meta', models.TextField()),
                ('gender', models.CharField(db_index=True, max_length=6L, null=True)),
                ('year_of_birth', models.IntegerField(db_index=True, null=True)),
                ('level_of_education', models.CharField(db_index=True, max_length=6L, null=True)),
                ('goals', models.TextField(null=True)),
                ('allow_certificate', models.BooleanField()),
                ('country', models.CharField(max_length=2L)),
                ('city', models.TextField()),
                ('bio', models.CharField(max_length=3000L, null=True)),
                ('profile_image_uploaded_at', models.DateTimeField(null=True)),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='edx.AuthUser')),
            ],
            options={
                'db_table': 'auth_userprofile',
            },
        ),
    ]