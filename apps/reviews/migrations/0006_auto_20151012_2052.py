# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('reviews', '0005_review_vendor_viewable'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reviewtoken',
            name='created_by',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
    ]
