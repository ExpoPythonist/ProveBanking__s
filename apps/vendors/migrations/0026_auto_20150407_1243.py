# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import djorm_pgarray.fields


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0004_auto_20150317_0723'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('locations', '0002_auto_20141207_0757'),
        ('vendors', '0025_auto_20150325_1435'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProcurementContact',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('categories', models.ManyToManyField(related_name='procurement_contacts', null=True, to='categories.Category', blank=True)),
                ('locations', models.ManyToManyField(related_name='procurement_contacts', null=True, to='locations.Location', blank=True)),
                ('user', models.ForeignKey(related_name='procurement_contacts', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterModelOptions(
            name='vendorcategories',
            options={'ordering': ('-allocation',)},
        ),
        migrations.AddField(
            model_name='vendor',
            name='contacts',
            field=models.ManyToManyField(related_name='contacts', null=True, to=settings.AUTH_USER_MODEL, blank=True),
            preserve_default=True,
        ),
    ]
