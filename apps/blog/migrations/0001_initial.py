# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Blog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('heading', models.CharField(max_length=255)),
                ('url', models.URLField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('kind', models.PositiveSmallIntegerField(default=1, choices=[(1, b'Main blog'), (2, b'Enterprise blog')])),
            ],
            options={
                'ordering': ('-created',),
            },
            bases=(models.Model,),
        ),
    ]
