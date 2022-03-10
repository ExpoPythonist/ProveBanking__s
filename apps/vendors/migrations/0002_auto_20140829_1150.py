# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('vendors', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='VendorInvitation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(related_name=b'invited_vendor_invitations', to=settings.AUTH_USER_MODEL)),
                ('vendor', models.ForeignKey(related_name=b'vendor_invitations', to='vendors.Vendor')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='vendorinvitation',
            unique_together=set([('vendor', 'user')]),
        ),
        migrations.AddField(
            model_name='vendor',
            name='invited_by',
            field=models.ManyToManyField(related_name=b'invited_vendors', through='vendors.VendorInvitation', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]
