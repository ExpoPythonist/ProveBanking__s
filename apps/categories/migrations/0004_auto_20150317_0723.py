# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import autoslug.fields


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0003_auto_20150103_0537'),
    ]

    operations = [
        migrations.CreateModel(
            name='CategoryType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(unique=True, max_length=256)),
                ('slug', autoslug.fields.AutoSlugField(unique=True, max_length=256, editable=False)),
                ('filter_enabled', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='category',
            name='custom_kind',
            field=models.ForeignKey(related_name='categories', blank=True, to='categories.CategoryType', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='category',
            name='kind',
            field=models.PositiveSmallIntegerField(default=1, choices=[(1, b'category'), (2, b'industry'), (1, b'skill'), (3, b'language'), (4, b'service'), (5, b'custom')]),
            preserve_default=True,
        ),
    ]
