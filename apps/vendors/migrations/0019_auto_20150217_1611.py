# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def migrate_vendor_kind(apps, schema_editor):
    vendor_model = apps.get_model('vendors', 'Vendor')
    kinds = {'Prospective': 3,
             'Approved': 2,
             'Preferred': 1}
    for vendor in vendor_model.objects.all():
        if vendor.kind:
            vendor.kynd = kinds.get(vendor.kind.name)
            vendor.save()


def nothing(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0018_auto_20150217_0752'),
    ]

    operations = [
        migrations.RunPython(migrate_vendor_kind, nothing),
    ]
