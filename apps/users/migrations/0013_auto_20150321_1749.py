# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgarray.fields
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0012_auto_20150309_0745'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='is_staffable',
            field=models.BooleanField(default=True, help_text='Can this person be staffed on projects?', verbose_name=b'Staffable'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='next_available',
            field=models.DateField(default=None, null=True, editable=False, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='phone',
            field=phonenumber_field.modelfields.PhoneNumberField(max_length=128, null=True, blank=True),
            preserve_default=True,
        ),
    ]
