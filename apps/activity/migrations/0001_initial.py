# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_pgjson.fields
import simple_activity.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('item_id', models.PositiveIntegerField()),
                ('target_id', models.PositiveIntegerField(null=True, blank=True)),
                ('verb', models.CharField(max_length=23)),
                ('published', models.DateTimeField(auto_now_add=True)),
                ('meta', django_pgjson.fields.JsonBField(default=simple_activity.models._default_action_meta, blank=True)),
                ('visibility', models.PositiveIntegerField(default=3, choices=[(1, b'Client'), (2, b'Vendors'), (3, b'Both vendors and client')])),
                ('actor', models.ForeignKey(related_name='activity', to=settings.AUTH_USER_MODEL)),
                ('item_type', models.ForeignKey(related_name='actions', to='contenttypes.ContentType')),
                ('target_type', models.ForeignKey(related_name='target_actions', blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'ordering': ('-published',),
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('content_type', models.ForeignKey(related_name='events', to='contenttypes.ContentType')),
                ('user', models.ForeignKey(related_name='events', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='event',
            unique_together=set([('content_type', 'object_id', 'user')]),
        ),
    ]
