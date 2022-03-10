# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0076_auto_20160421_1635'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='clientreference',
            options={'ordering': ('-is_fulfilled', '-client__client_quality_score')},
        ),
    ]
