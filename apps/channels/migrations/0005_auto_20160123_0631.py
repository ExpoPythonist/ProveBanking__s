# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('channels', '0004_auto_20141205_0309'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='channel',
            name='vendors',
        ),
        migrations.AddField(
            model_name='channel',
            name='users',
            field=models.ManyToManyField(related_name='channels', verbose_name=b'members', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='message',
            name='viewed',
            field=models.ManyToManyField(related_name='read_messages', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
