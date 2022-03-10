# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import picklefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0002_auto_20150528_0907'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='alexa_rank',
            field=models.PositiveIntegerField(null=True, verbose_name=b'Alexa Rank', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='client',
            name='annual_revenue',
            field=models.PositiveIntegerField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='client',
            name='clearbit_data',
            field=picklefield.fields.PickledObjectField(null=True, editable=False, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='client',
            name='client_quality_score',
            field=models.DecimalField(null=True, verbose_name=b'Client Quality Score', max_digits=4, decimal_places=2, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='client',
            name='employee_count',
            field=models.PositiveIntegerField(null=True, verbose_name=b'Employee Count', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='client',
            name='founded_date',
            field=models.DateField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='client',
            name='google_pagerank',
            field=models.PositiveIntegerField(null=True, verbose_name=b'Google PageRank', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='client',
            name='market_cap',
            field=models.PositiveIntegerField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='client',
            name='registration_type',
            field=models.CharField(blank=True, max_length=100, verbose_name=b'Registration Type', choices=[(b'public', b'Public'), (b'private', b'Private')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='client',
            name='twitter_followers',
            field=models.PositiveIntegerField(null=True, verbose_name=b'Twitter Followers', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='client',
            name='website',
            field=models.URLField(default=b'', max_length=127),
            preserve_default=True,
        ),
    ]
