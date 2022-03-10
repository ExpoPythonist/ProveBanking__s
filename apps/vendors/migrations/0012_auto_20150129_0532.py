# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgarray.fields
import vendors.models


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0003_auto_20150103_0537'),
        ('vendors', '0011_auto_20150122_0605'),
    ]

    operations = [
        migrations.CreateModel(
            name='VendorServices',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('allocation', models.PositiveSmallIntegerField(default=0, verbose_name='Service percentage')),
                ('service', models.ForeignKey(to='categories.Category')),
                ('vendor', models.ForeignKey(related_name=b'vendor_services', to='vendors.Vendor')),
            ],
            options={
                'ordering': ('service',),
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='vendorservices',
            unique_together=set([('vendor', 'service')]),
        ),
        migrations.AddField(
            model_name='vendor',
            name='service',
            field=models.ManyToManyField(related_name=b'vendor_service', through='vendors.VendorServices', to='categories.Category'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='vendor',
            name='pending_edit_steps',
            field=djorm_pgarray.fields.ArrayField(default=vendors.models.default_pending_steps, verbose_name='Pending steps'),
        ),
        migrations.AlterField(
            model_name='vendorcategories',
            name='allocation',
            field=models.PositiveSmallIntegerField(default=0, verbose_name='Skill percentage'),
        ),
    ]
