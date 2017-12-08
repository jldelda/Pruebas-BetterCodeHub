# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-03 03:59
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('control_panel', '0005_course_language'),
    ]

    operations = [
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('id', models.CharField(max_length=40, primary_key=True, serialize=False)),
                ('enable', models.BooleanField(default=True)),
                ('trigger_time', models.DateTimeField()),
                ('open_rate', models.FloatField(blank=True)),
                ('click_rate', models.FloatField(blank=True)),
                ('num_emails', models.IntegerField(blank=True)),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='control_panel.Course')),
            ],
        ),
        migrations.CreateModel(
            name='CampaignGenerator',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('trigger_time', models.DateTimeField()),
                ('certification_index', models.ManyToManyField(blank=True, to='control_panel.CertificationIndex')),
            ],
        ),
        migrations.CreateModel(
            name='Template',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=128)),
            ],
        ),
        migrations.AddField(
            model_name='compoundindex',
            name='courses',
            field=models.ManyToManyField(to='control_panel.Course'),
        ),
        migrations.AddField(
            model_name='campaigngenerator',
            name='compound_index',
            field=models.ManyToManyField(blank=True, to='control_panel.CompoundIndex'),
        ),
        migrations.AddField(
            model_name='campaigngenerator',
            name='courses',
            field=models.ManyToManyField(to='control_panel.Course'),
        ),
        migrations.AddField(
            model_name='campaigngenerator',
            name='progress_index',
            field=models.ManyToManyField(blank=True, to='control_panel.ProgressIndex'),
        ),
        migrations.AddField(
            model_name='campaigngenerator',
            name='qualification_index',
            field=models.ManyToManyField(blank=True, to='control_panel.QualificationIndex'),
        ),
        migrations.AddField(
            model_name='campaigngenerator',
            name='test_emails',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL),
        ),
    ]
