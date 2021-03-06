# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-10-24 03:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AuthUser',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('username', models.CharField(max_length=30L, unique=True)),
                ('first_name', models.CharField(max_length=30L)),
                ('last_name', models.CharField(max_length=30L)),
                ('email', models.CharField(max_length=75L, unique=True)),
                ('password', models.CharField(max_length=128L)),
                ('is_staff', models.IntegerField()),
                ('is_active', models.IntegerField()),
                ('is_superuser', models.IntegerField()),
                ('last_login', models.DateTimeField()),
                ('date_joined', models.DateTimeField()),
            ],
            options={
                'db_table': 'auth_user',
            },
        ),
    ]
