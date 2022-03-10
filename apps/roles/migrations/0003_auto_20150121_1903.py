# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def fix_role_colors(apps, schema_editor):
    Role = apps.get_model("roles", "Role")
    Role.objects.filter(color='#FFFFFF').update(color='#F6F5F4')


class Migration(migrations.Migration):

    dependencies = [
        ('roles', '0002_role_color'),
    ]

    operations = [
        migrations.RunPython(fix_role_colors,
                             lambda apps, schema_editor: None)
    ]
