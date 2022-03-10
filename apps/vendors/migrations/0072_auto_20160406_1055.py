# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings
import uuidfield.fields
import phonenumber_field.modelfields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('categories', '0006_categorytype_vendor_editable'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('vendors', '0041_auto_20150714_1026_squashed_0071_auto_20160405_0521'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bid',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('bid', models.DecimalField(null=True, max_digits=20, decimal_places=2, blank=True)),
                ('description', models.TextField(blank=True)),
                ('winner', models.BooleanField(default=False)),
                ('masked_phone', phonenumber_field.modelfields.PhoneNumberField(max_length=128, blank=True)),
                ('uuid', uuidfield.fields.UUIDField(default=uuid.uuid4, max_length=32, editable=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('date_deleted', models.DateTimeField(null=True, editable=False, blank=True)),
            ],
            options={
                'ordering': ('date_created',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('message', models.TextField(blank=True)),
                ('uuid', uuidfield.fields.UUIDField(default=uuid.uuid4, max_length=32, editable=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('date_deleted', models.DateTimeField(null=True, editable=False, blank=True)),
                ('bid', models.ForeignKey(related_name='messages', to='vendors.Bid')),
                ('sender', models.ForeignKey(related_name='rfp_messages', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('date_created',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RFP',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('open_rfp', models.BooleanField(default=False)),
                ('question', models.CharField(max_length=1000)),
                ('description', models.TextField(blank=True)),
                ('masked', models.BooleanField(default=False)),
                ('masked_phone', phonenumber_field.modelfields.PhoneNumberField(max_length=128, blank=True)),
                ('masked_expiry', models.CharField(blank=True, max_length=10, choices=[('1 hour', '1 hour'), ('5 hours', '5 hours'), ('24 hours', '24 hours'), ('2 days', '2 days'), ('1 week', '1 week')])),
                ('notif_call', models.BooleanField(default=False, verbose_name='Allow call?')),
                ('notif_text', models.BooleanField(default=True, verbose_name='Allow text?')),
                ('notif_email', models.BooleanField(default=True, verbose_name='Allow email?')),
                ('uuid', uuidfield.fields.UUIDField(default=uuid.uuid4, max_length=32, editable=False)),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('date_modified', models.DateTimeField(auto_now=True)),
                ('date_deleted', models.DateTimeField(null=True, editable=False, blank=True)),
                ('categories', models.ManyToManyField(related_name='rfps', to='categories.Category', blank=True)),
                ('client', models.ForeignKey(related_name='rfps', to=settings.AUTH_USER_MODEL)),
                ('vendors', models.ManyToManyField(related_name='rfps', through='vendors.Bid', to='vendors.Vendor', blank=True)),
            ],
            options={
                'ordering': ('date_created',),
                'verbose_name': 'RFP',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='bid',
            name='rfp',
            field=models.ForeignKey(related_name='bids', to='vendors.RFP'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bid',
            name='vendor',
            field=models.ForeignKey(related_name='bids', to='vendors.Vendor'),
            preserve_default=True,
        ),
    ]
