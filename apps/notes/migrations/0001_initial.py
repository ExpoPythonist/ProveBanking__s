# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import notes.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Note',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.TextField()),
                ('object_id', models.PositiveIntegerField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('content_type', models.ForeignKey(to='contenttypes.ContentType')),
                ('posted_by', models.ForeignKey(related_name=b'notes_set', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created',),
                'db_table': 'notes',
                'verbose_name': 'note',
                'verbose_name_plural': 'notes',
            },
            bases=(models.Model, notes.models.NoteMixin),
        ),
        migrations.CreateModel(
            name='NoteComment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.TextField()),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('note', models.ForeignKey(related_name=b'comments', to='notes.Note')),
                ('posted_by', models.ForeignKey(related_name=b'note_comments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('created',),
                'db_table': 'notes_comments',
                'verbose_name': 'note comment',
                'verbose_name_plural': 'note comments',
            },
            bases=(models.Model, notes.models.NoteMixin),
        ),
    ]
