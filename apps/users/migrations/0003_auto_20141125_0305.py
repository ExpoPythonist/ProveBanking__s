# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def fix_usernames(apps, schema_editor):
    U = apps.get_model("users", "User")
    for u in U.objects.all():
        u.username = u.username.lower()
        u.save()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20141016_0605'),
    ]

    operations = [
        migrations.RunPython(fix_usernames, lambda a, s: None)
    ]
