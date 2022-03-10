# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgarray.fields


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0022_auto_20150223_1937'),
    ]

    operations = [
        migrations.CreateModel(
            name='VendorScoreAggregate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('acceptance_rate', models.DecimalField(null=True, max_digits=2, decimal_places=1, blank=True)),
                ('response_time', models.DecimalField(null=True, max_digits=2, decimal_places=1, blank=True)),
                ('user_rating', models.DecimalField(null=True, max_digits=2, decimal_places=1, blank=True)),
                ('vendor', models.OneToOneField(related_name='score_aggregate', to='vendors.Vendor')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
