# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgarray.fields
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_auto_20150128_0409'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='phone',
            field=phonenumber_field.modelfields.PhoneNumberField(max_length=128, null=True),
            preserve_default=True,
        ),
    ]
