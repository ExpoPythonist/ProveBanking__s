# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import djorm_pgarray.fields
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0015_auto_20150323_1233'),
    ]

    operations = [
        migrations.CreateModel(
            name='SignupToken',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', django_extensions.db.fields.UUIDField(max_length=36, editable=False, blank=True)),
                ('email', models.EmailField(max_length=254, verbose_name='email address')),
                ('expires_at', models.DateTimeField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('is_verified', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]
