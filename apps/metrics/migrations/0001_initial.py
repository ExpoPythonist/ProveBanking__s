# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Metric',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('kind', models.PositiveSmallIntegerField(choices=[(1, b'response'), (2, b'acceptance'), (3, b'user_rating')])),
                ('score', models.DecimalField(max_digits=2, decimal_places=1)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('object_id', models.PositiveIntegerField()),
                ('target_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(related_name='metric', to='contenttypes.ContentType')),
                ('target_type', models.ForeignKey(related_name='metric_owned', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MetricAggregate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('kind', models.PositiveSmallIntegerField(choices=[(1, b'response'), (2, b'acceptance'), (3, b'user_rating')])),
                ('start_date', models.DateField()),
                ('score', models.DecimalField(null=True, max_digits=2, decimal_places=1)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(related_name='metric_aggregate', to='contenttypes.ContentType')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
