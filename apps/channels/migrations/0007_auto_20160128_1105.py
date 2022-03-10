# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('channels', '0006_auto_20160127_1520'),
    ]

    operations = [
        migrations.AlterField(
            model_name='message',
            name='posted_by',
            field=models.ForeignKey(related_name='messages', to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
    ]
