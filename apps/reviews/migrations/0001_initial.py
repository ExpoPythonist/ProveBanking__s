# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import autoslug.fields
import vlkjsonfield.fields
from django.conf import settings
import reviews.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Metric',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=127, verbose_name='metric name')),
                ('slug', autoslug.fields.AutoSlugField(editable=False)),
                ('help_text', models.TextField(default=b'', verbose_name='help text', blank=True)),
                ('weight', models.PositiveSmallIntegerField(default=0)),
                ('kind', models.CharField(default=b'rating', max_length=127, choices=[(b'rating', b'Rating (1 - 5 stars)'), (b'nps', b'Net Promoter Score')])),
                ('metric_data', vlkjsonfield.fields.VLKJSONField(default=reviews.models._get_default_metric_data)),
                ('source', models.PositiveSmallIntegerField(default=3, choices=[(1, b'Calculated by Proven'), (3, b'Manually entered by client'), (4, b'Manually entered by vendor')])),
                ('is_deleted', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('content_type', models.ForeignKey(related_name=b'metrics', to='contenttypes.ContentType')),
            ],
            options={
                'ordering': ('-weight', 'id'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='MetricReview',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('score', models.DecimalField(max_digits=2, decimal_places=1)),
                ('metric', models.ForeignKey(related_name=b'review_metrics', to='reviews.Metric')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Review',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('remarks', models.TextField(default=b'', verbose_name='remarks', blank=True)),
                ('score', models.DecimalField(null=True, max_digits=2, decimal_places=1, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('content_type', models.ForeignKey(related_name=b'reviews', to='contenttypes.ContentType')),
                ('metrics', models.ManyToManyField(to='reviews.Metric', through='reviews.MetricReview')),
                ('posted_by', models.ForeignKey(related_name=b'reviews_submitted', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created',),
                'get_latest_by': 'created',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='metricreview',
            name='review',
            field=models.ForeignKey(related_name=b'review_metrics', to='reviews.Review'),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='metric',
            unique_together=set([('content_type', 'slug')]),
        ),
    ]
