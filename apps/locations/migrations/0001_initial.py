# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('city', models.CharField(max_length=255, verbose_name='location')),
                ('slug', models.TextField(unique=True, null=True, blank=True)),
            ],
            options={
                'ordering': ('city',),
            },
            bases=(models.Model,),
        ),
    ]
