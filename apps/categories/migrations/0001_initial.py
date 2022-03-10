# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import autoslug.fields
import categories.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=511)),
                ('slug', models.TextField(null=True, blank=True)),
                ('kind', models.PositiveSmallIntegerField(default=1, choices=[(1, b'category'), (2, b'industry'), (1, b'skill')])),
                ('parent', models.ForeignKey(related_name=b'categories', blank=True, to='categories.Category', null=True)),
            ],
            options={
                'verbose_name': 'category',
                'verbose_name_plural': 'categories',
            },
            bases=(models.Model, categories.models.CategoryKindMixin),
        ),
        migrations.CreateModel(
            name='SkillLevel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('label', models.CharField(unique=True, max_length=256)),
                ('slug', autoslug.fields.AutoSlugField(unique=True, max_length=256, editable=False)),
                ('level', models.PositiveSmallIntegerField()),
            ],
            options={
                'ordering': ('-level',),
                'verbose_name': 'skill level',
                'verbose_name_plural': 'skill levels',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='category',
            unique_together=set([('slug', 'kind')]),
        ),
    ]
