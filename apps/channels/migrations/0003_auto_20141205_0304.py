# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def populate_created_by(apps, schema_editor):
    Channel = apps.get_model("channels", "Channel")
    User = apps.get_model("users", "User")
    try:
        user = User.objects.filter(vendor=None)[0]
    except IndexError:
        return

    Channel.objects.update(created_by=user)


class Migration(migrations.Migration):

    dependencies = [
        ('channels', '0002_auto_20141205_0301'),
    ]

    operations = [
        migrations.RunPython(populate_created_by,
                             lambda apps, schema_editor: None,)
    ]
