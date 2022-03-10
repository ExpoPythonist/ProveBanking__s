# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
        ('vendors', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Channel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(default=b'', max_length=b'127', blank=True)),
                ('object_id', models.PositiveIntegerField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('content_type', models.ForeignKey(related_name=b'channels', to='contenttypes.ContentType')),
                ('vendors', models.ManyToManyField(related_name=b'vendors', to='vendors.Vendor')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('body', models.TextField(verbose_name=b'Message')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('channel', models.ForeignKey(related_name=b'messages', to='channels.Channel')),
                ('mentions', models.ManyToManyField(related_name=b'mentions', to=settings.AUTH_USER_MODEL)),
                ('posted_by', models.ForeignKey(related_name=b'messages', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('created',),
                'get_latest_by': 'created',
            },
            bases=(models.Model,),
        ),
    ]
