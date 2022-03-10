# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0035_auto_20150515_0722'),
    ]

    operations = [
        migrations.AlterField(
            model_name='certverification',
            name='email_msg',
            field=models.TextField(max_length=1000, null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='clientreference',
            name='billing_private',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='portfolioitem',
            name='owners',
            field=models.ManyToManyField(related_name='owned_portfolio', null=True, to=settings.AUTH_USER_MODEL, blank=True),
            preserve_default=True,
        ),
    ]
