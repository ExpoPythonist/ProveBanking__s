# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import storages.backends.s3boto
import users.models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0024_auto_20160505_1718'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='resume',
            field=models.FileField(storage=storages.backends.s3boto.S3BotoStorage(querystring_expire=600, bucket=b'proven-cc', querystring_auth=True, acl=b'private'), null=True, upload_to=users.models._get_resume_upload_path),
            preserve_default=True,
        ),
    ]
