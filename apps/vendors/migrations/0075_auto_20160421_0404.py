# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('certs', '0002_auto_20160420_1306'),
        ('vendors', '0074_auto_20160420_1306'),
    ]

    operations = [
        migrations.CreateModel(
            name='InsuranceVerification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('extent', models.IntegerField(null=True, choices=[(1, '\xe22.6 million'), (2, '\xe26.5 million'), (3, 'Other (please specify)')])),
                ('expiry_date', models.DateTimeField(null=True, blank=True)),
                ('remind_me', models.BooleanField(default=False)),
                ('policy_document', models.FileField(null=True, upload_to=b'insurance/', blank=True)),
                ('url', models.URLField(default='', max_length=255, blank=True)),
                ('email', models.EmailField(max_length=75, null=True, blank=True)),
                ('email_msg', models.TextField(max_length=1000, null=True, blank=True)),
                ('token', models.CharField(max_length=40)),
                ('is_fulfilled', models.BooleanField(default=False)),
                ('is_verified', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(related_name='insurance_verifications', to=settings.AUTH_USER_MODEL)),
                ('insurance', models.ForeignKey(to='certs.Cert')),
                ('vendor', models.ForeignKey(related_name='insurance_verifications', to='vendors.Vendor')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.RemoveField(
            model_name='certverification',
            name='cert_type',
        ),
        migrations.RemoveField(
            model_name='certverification',
            name='expiry_date',
        ),
    ]
