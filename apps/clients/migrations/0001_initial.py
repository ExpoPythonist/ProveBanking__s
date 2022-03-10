# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import autoslug.fields
import sorl.thumbnail.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Client',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('slug', autoslug.fields.AutoSlugField(unique=True, null=True, editable=False)),
                ('logo', sorl.thumbnail.fields.ImageField(upload_to=b'images/logo/', null=True, verbose_name='Company logo', blank=True)),
                ('size', models.PositiveSmallIntegerField(null=True, choices=[(1, b'1 - 5'), (2, b'5 - 25'), (3, b'25 - 50'), (4, b'50 - 100'), (5, b'100 - 1,000'), (6, b'1,000 - 10,000'), (7, b'10,000 - 100,000'), (8, b'100,000+')])),
                ('is_partner', models.BooleanField(default=False)),
                ('salesforce_token', models.CharField(max_length=255, null=True, blank=True)),
                ('salesforce_instance', models.CharField(max_length=255, null=True, blank=True)),
                ('website', models.URLField(default=b'', max_length=127, blank=True)),
                ('email_domain', models.CharField(default=b'', max_length=255)),
                ('created_by', models.ForeignKey(related_name='clients_created', to=settings.AUTH_USER_MODEL, null=True)),
                ('industries', models.ManyToManyField(related_name='clients', to='categories.Category')),
                ('services', models.ManyToManyField(related_name='client_services', to='categories.Category')),
                ('skills', models.ManyToManyField(related_name='client_skills', to='categories.Category')),
                ('users', models.ManyToManyField(related_name='clients', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('name',),
            },
            bases=(models.Model,),
        ),
    ]
