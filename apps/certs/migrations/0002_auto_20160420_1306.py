# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('certs', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cert',
            name='kind',
            field=models.PositiveSmallIntegerField(default=1, choices=[(1, b'cert'), (2, b'partner'), (3, b'insurance')]),
            preserve_default=True,
        ),
    ]
