# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-13 21:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('xwing_data', '0010_auto_20170313_2140'),
    ]

    operations = [
        migrations.AddField(
            model_name='upgrade',
            name='grants',
            field=models.ManyToManyField(to='xwing_data.Grant'),
        ),
    ]