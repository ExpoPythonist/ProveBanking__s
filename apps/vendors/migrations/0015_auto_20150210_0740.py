# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgarray.fields


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0014_auto_20150203_1536'),
    ]

    operations = [
        migrations.CreateModel(
            name='VendorKind',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=254)),
                ('slug', models.TextField(unique=True, null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='vendor',
            name='kind',
            field=models.ForeignKey(related_name='vendors', blank=True, to='vendors.VendorKind', null=True),
            preserve_default=True,
        ),
    ]
