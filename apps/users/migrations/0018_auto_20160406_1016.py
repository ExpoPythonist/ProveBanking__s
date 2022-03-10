# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_pgjson.fields
import djorm_pgarray.fields
import storages.backends.s3boto
import users.models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0017_auto_20150716_0720'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='divisions',
            field=models.ManyToManyField(related_name='users', through='users.UserDivisionRel', to='divisions.Division', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='meta',
            field=django_pgjson.fields.JsonBField(default=users.models._default_user_meta, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='pending_setup_steps',
            field=djorm_pgarray.fields.ArrayField(default='{1, 3}', verbose_name='Pending steps'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='user',
            name='resume',
            field=models.FileField(storage=storages.backends.s3boto.S3BotoStorage(querystring_expire=600, bucket=b'dev-proven-cc', querystring_auth=True, acl=b'private'), null=True, upload_to=users.models._get_resume_upload_path),
            preserve_default=True,
        ),
    ]
