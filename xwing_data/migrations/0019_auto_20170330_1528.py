# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-30 14:28
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('xwing_data', '0018_auto_20170328_1704'),
    ]

    operations = [
        migrations.RenameField(
            model_name='statisticset',
            old_name='shield',
            new_name='shields',
        ),
    ]
