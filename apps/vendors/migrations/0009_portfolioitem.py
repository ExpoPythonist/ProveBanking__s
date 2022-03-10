# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('categories', '0003_auto_20150103_0537'),
        ('locations', '0002_auto_20141207_0757'),
        ('vendors', '0008_auto_20150105_1519'),
    ]

    operations = [
        migrations.CreateModel(
            name='PortfolioItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True)),
                ('start_date', models.DateField(null=True)),
                ('end_date', models.DateField(null=True)),
                ('location', models.ForeignKey(related_name=b'portfolio', blank=True, to='locations.Location', null=True)),
                ('owners', models.ManyToManyField(related_name=b'owned_portfolio', to=settings.AUTH_USER_MODEL, blank=True)),
                ('skills', models.ManyToManyField(related_name=b'portfolio', to='categories.Category')),
                ('vendor', models.ForeignKey(related_name=b'portfolio', to='vendors.Vendor')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
