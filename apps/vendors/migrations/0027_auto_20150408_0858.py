# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgarray.fields


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0026_auto_20150407_1243'),
    ]

    operations = [
        migrations.AddField(
            model_name='procurementcontact',
            name='vendors',
            field=models.ManyToManyField(to='vendors.Vendor', null=True, blank=True),
            preserve_default=True,
        ),
    ]
