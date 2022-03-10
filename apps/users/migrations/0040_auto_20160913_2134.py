# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-09-13 21:34
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0039_auto_20160804_0518'),
    ]

    operations = [
        migrations.AlterField(
            model_name='signuptoken',
            name='uuid',
            field=models.UUIDField(blank=True, db_index=True, default=uuid.uuid4, editable=False),
        ),
        migrations.AlterField(
            model_name='userinvitation',
            name='uuid',
            field=models.UUIDField(blank=True, db_index=True, default=uuid.uuid4, editable=False),
        ),
    ]
