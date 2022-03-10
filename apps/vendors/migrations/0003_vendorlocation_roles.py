# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('roles', '0001_initial'),
        ('vendors', '0002_auto_20140829_1150'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendorlocation',
            name='roles',
            field=models.ManyToManyField(to='roles.Role'),
            preserve_default=True,
        ),
    ]
