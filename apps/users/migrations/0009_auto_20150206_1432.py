# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('divisions', '0002_division_slug'),
        ('users', '0008_merge'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserDivisionRel',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_admin', models.BooleanField(default=False)),
                ('division', models.ForeignKey(related_name='user_rels', to='divisions.Division')),
                ('user', models.ForeignKey(related_name='division_rels', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='user',
            name='divisions',
        ),
    ]
