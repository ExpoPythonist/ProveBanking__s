# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import vlkjsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Answer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('answer', models.IntegerField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('answered_by', models.ForeignKey(related_name=b'answers', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('question', models.TextField()),
                ('answer_type', models.PositiveSmallIntegerField(choices=[(1, b'Numeric'), (2, b'Boolean'), (3, b'Choice')])),
                ('definitions', vlkjsonfield.fields.VLKJSONField(default={})),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='SLA',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=127)),
                ('expires', models.DateTimeField(null=True, blank=True)),
                ('due_date', models.DateTimeField(null=True, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='question',
            name='sla',
            field=models.ForeignKey(related_name=b'questions', to='slas.SLA'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='answer',
            name='question',
            field=models.ForeignKey(related_name=b'answers', to='slas.Question'),
            preserve_default=True,
        ),
    ]
