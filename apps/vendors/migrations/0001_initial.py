# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import autoslug.fields
import sorl.thumbnail.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('locations', '__first__'),
        ('categories', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Vendor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='Company name')),
                ('slug', autoslug.fields.AutoSlugField(unique=True, editable=False)),
                ('email', models.EmailField(unique=True, max_length=75, verbose_name='Email')),
                ('logo', sorl.thumbnail.fields.ImageField(upload_to=b'images/logo/', null=True, verbose_name='Company logo', blank=True)),
                ('website', models.URLField(default=b'', max_length=127, verbose_name='Website', blank=True)),
                ('twitter', models.CharField(default=b'', max_length=127, verbose_name='Twitter', blank=True)),
                ('facebook', models.URLField(default=b'', max_length=255, verbose_name='Facebook', blank=True)),
                ('linkedin', models.URLField(default=b'', max_length=255, verbose_name='Linkedin', blank=True)),
                ('partner_since', models.DateField(null=True, blank=True)),
                ('joined_on', models.DateTimeField(null=True, blank=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('avg_score', models.DecimalField(null=True, max_digits=2, decimal_places=1, blank=True)),
                ('categories', models.ManyToManyField(related_name=b'vendors', to='categories.Category')),
                ('industries', models.ManyToManyField(related_name=b'companies', to='categories.Category')),
            ],
            options={
                'ordering': ('-avg_score',),
            },
            bases=(models.Model,),
        ),

        migrations.CreateModel(
            name='VendorLocation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('num_resources', models.PositiveSmallIntegerField(default=1, verbose_name='Number of employees')),
                ('location', models.ForeignKey(to='locations.Location')),
                ('vendor', models.ForeignKey(to='vendors.Vendor')),
            ],
            options={
                'ordering': ('location',),
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='vendorlocation',
            unique_together=set([('vendor', 'location')]),
        ),

        migrations.AddField(
            model_name='vendor',
            name='locations',
            field=models.ManyToManyField(related_name=b'vendors', through='vendors.VendorLocation', to='locations.Location'),
            preserve_default=True,
        ),
    ]
