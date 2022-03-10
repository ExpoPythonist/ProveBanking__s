# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
        ('reviews', '0002_review_anonymous'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReviewToken',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('uuid', django_extensions.db.fields.UUIDField(max_length=36, editable=False, blank=True)),
                ('object_id', models.PositiveIntegerField()),
                ('email', models.EmailField(max_length=254, verbose_name='email address')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('is_used', models.BooleanField(default=False)),
                ('content_type', models.ForeignKey(related_name='review_token', to='contenttypes.ContentType')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='review',
            name='token',
            field=models.ForeignKey(related_name='review', blank=True, to='reviews.ReviewToken', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='review',
            name='posted_by',
            field=models.ForeignKey(related_name='reviews_submitted', blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
    ]
