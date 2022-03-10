# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgarray.fields
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_auto_20150206_1443'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='userdivisionrel',
            unique_together=set([('user', 'division')]),
        ),
    ]
