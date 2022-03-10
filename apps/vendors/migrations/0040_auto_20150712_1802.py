# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0006_categorytype_vendor_editable'),
        ('vendors', '0039_auto_20150630_1702'),
    ]

    operations = [
        migrations.CreateModel(
            name='VendorCustomKind',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('allocation', models.PositiveSmallIntegerField(default=0, verbose_name='Category percentage')),
                ('category', models.ForeignKey(to='categories.Category')),
                ('vendor', models.ForeignKey(related_name='vendor_custom', to='vendors.Vendor')),
            ],
            options={
                'ordering': ('-allocation',),
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='vendorcustomkind',
            unique_together=set([('vendor', 'category')]),
        ),
    ]
