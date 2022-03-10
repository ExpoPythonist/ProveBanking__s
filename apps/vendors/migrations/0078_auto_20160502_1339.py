# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0077_auto_20160501_1320'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rfp',
            name='notif_email',
            field=models.BooleanField(default=True, verbose_name='Notify through email?'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='rfp',
            name='notif_text',
            field=models.BooleanField(default=True, verbose_name='Notify through text?'),
            preserve_default=True,
        ),
    ]
