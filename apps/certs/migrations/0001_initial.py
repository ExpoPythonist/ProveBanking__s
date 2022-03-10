# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import autoslug.fields


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Cert',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=127)),
                ('slug', autoslug.fields.AutoSlugField(unique=True, null=True, editable=False)),
                ('kind', models.PositiveSmallIntegerField(default=1, choices=[(1, b'cert'), (2, b'partner')])),
                ('client', models.ForeignKey(related_name='certs', to='clients.Client', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
