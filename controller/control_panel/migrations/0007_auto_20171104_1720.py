# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-04 17:20
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('control_panel', '0006_auto_20171103_0359'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='certificationindex',
            name='courses',
        ),
        migrations.RemoveField(
            model_name='compoundindex',
            name='courses',
        ),
        migrations.RemoveField(
            model_name='progressindex',
            name='courses',
        ),
        migrations.RemoveField(
            model_name='qualificationindex',
            name='courses',
        ),
        migrations.AddField(
            model_name='certificationindex',
            name='template',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='control_panel.Template'),
        ),
        migrations.AddField(
            model_name='compoundindex',
            name='template',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='control_panel.Template'),
        ),
        migrations.AddField(
            model_name='progressindex',
            name='template',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='control_panel.Template'),
        ),
        migrations.AddField(
            model_name='qualificationindex',
            name='template',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='control_panel.Template'),
        ),
    ]
