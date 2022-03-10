# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('channels', '0003_auto_20141205_0304'),
    ]

    operations = [
        migrations.AlterField(
            model_name='channel',
            name='created_by',
            field=models.ForeignKey(related_name=b'created_channels', to=settings.AUTH_USER_MODEL),
        ),
     ]
