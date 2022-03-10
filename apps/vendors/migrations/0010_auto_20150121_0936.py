# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0009_portfolioitem'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vendorcategories',
            name='vendor',
            field=models.ForeignKey(related_name=b'vendor_skills', to='vendors.Vendor'),
        ),
        migrations.AlterField(
            model_name='vendorlocation',
            name='vendor',
            field=models.ForeignKey(related_name=b'vendor_locations', to='vendors.Vendor'),
        ),
        migrations.AlterField(
            model_name='vendorroles',
            name='vendor',
            field=models.ForeignKey(related_name=b'vendor_roles', to='vendors.Vendor'),
        ),
    ]
