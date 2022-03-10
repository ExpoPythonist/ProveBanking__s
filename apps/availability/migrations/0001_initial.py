# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UpdateRequest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('requested_by', models.ManyToManyField(related_name=b'requested_availability_updates', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(related_name=b'update_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Week',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date', models.DateField()),
                ('allocation', models.IntegerField(default=0)),
                ('proposed', models.ManyToManyField(related_name=b'availability_weeks', to='projects.ProposedResource')),
                ('user', models.ForeignKey(related_name=b'availability_weeks', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('date',),
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='week',
            unique_together=set([('user', 'date')]),
        ),
    ]
