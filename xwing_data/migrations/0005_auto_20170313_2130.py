# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-13 21:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xwing_data', '0004_auto_20170313_2128'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pilot',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to=''),
        ),
        migrations.AlterField(
            model_name='upgrade',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to=''),
        ),
    ]