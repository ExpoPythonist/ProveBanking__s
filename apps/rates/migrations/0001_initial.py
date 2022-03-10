# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('roles', '0001_initial'),
        ('locations', '__first__'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('vendors', '0001_initial'),
        ('categories', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Rate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cost', models.DecimalField(max_digits=10, decimal_places=0)),
                ('unit', models.PositiveSmallIntegerField(default=2, choices=[(2, b'per hour'), (3, b'per day'), (4, b'per week')])),
                ('is_global', models.BooleanField(default=True)),
                ('location', models.ForeignKey(to='locations.Location', null=True)),
                ('role', models.ForeignKey(to='roles.Role', null=True)),
                ('skill_level', models.ForeignKey(to='categories.SkillLevel', null=True)),
                ('user', models.OneToOneField(related_name=b'rate', null=True, blank=True, to=settings.AUTH_USER_MODEL)),
                ('vendor', models.ForeignKey(related_name=b'rates', blank=True, to='vendors.Vendor', null=True)),
            ],
            options={
                'db_table': 'rates',
                'verbose_name': 'rate',
                'verbose_name_plural': 'rates',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='rate',
            unique_together=set([('location', 'skill_level', 'role', 'vendor', 'user', 'is_global')]),
        ),
    ]
