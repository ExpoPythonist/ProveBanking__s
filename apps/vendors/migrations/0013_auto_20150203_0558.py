# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import djorm_pgarray.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('vendors', '0012_auto_20150129_0532'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendor',
            name='client_contact',
            field=models.ForeignKey(related_name=b'vendor_contact', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
    ]
