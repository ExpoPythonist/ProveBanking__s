# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def combine_locations(apps, schema_editor):
    PortfolioItem = apps.get_model("vendors", "PortfolioItem")
    for project in PortfolioItem.objects.all():
        if project.location:
            location = project.location
            project.locations.add(location)
            project.save()


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0031_auto_20150507_0901'),
    ]

    operations = [
        migrations.RunPython(combine_locations),
    ]
