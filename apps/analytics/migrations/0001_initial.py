# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PageView',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.PositiveIntegerField()),
                ('count', models.IntegerField(default=1)),
                ('by', models.ForeignKey(related_name='page_views', to=settings.AUTH_USER_MODEL)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='pageview',
            unique_together=set([('content_type', 'object_id', 'by')]),
        ),
        migrations.AlterIndexTogether(
            name='pageview',
            index_together=set([('content_type', 'object_id')]),
        ),
    ]
