# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import slas.models
import vlkjsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('slas', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Response',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('answer', models.IntegerField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('answered_by', models.ForeignKey(related_name=b'sla_responses', to=settings.AUTH_USER_MODEL)),
                ('sla', models.ForeignKey(related_name=b'responses', to='slas.SLA')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='answer',
            name='answered_by',
        ),
        migrations.RemoveField(
            model_name='answer',
            name='question',
        ),
        migrations.DeleteModel(
            name='Answer',
        ),
        migrations.RemoveField(
            model_name='question',
            name='sla',
        ),
        migrations.DeleteModel(
            name='Question',
        ),
        migrations.RemoveField(
            model_name='sla',
            name='name',
        ),
        migrations.AddField(
            model_name='sla',
            name='answer_type',
            field=models.PositiveSmallIntegerField(default=1, choices=[(1, b'Numeric'), (2, b'Boolean'), (3, b'Choice')]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='sla',
            name='definitions',
            field=vlkjsonfield.fields.VLKJSONField(default=slas.models._get_default_definitions),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='sla',
            name='question',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
    ]
