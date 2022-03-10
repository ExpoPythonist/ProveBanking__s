# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0003_vendorlocation_roles'),
    ]

    operations = [
        migrations.CreateModel(
            name='VendorType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=254)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='vendor',
            name='type',
            field=models.ForeignKey(related_name=b'vendors', blank=True, to='vendors.VendorType', null=True),
            preserve_default=True,
        ),
    ]
