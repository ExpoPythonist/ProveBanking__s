# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0022_auto_20160501_1317'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_bid_change',
            field=models.BooleanField(default=True, verbose_name=b'E-MAIL: When a vendor posts a bid'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='email_bid_lose',
            field=models.BooleanField(default=True, verbose_name=b'E-MAIL: When my bid loses the contract'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='email_bid_win',
            field=models.BooleanField(default=True, verbose_name=b'E-MAIL: When my bid wins the contract'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='email_rfp_message',
            field=models.BooleanField(default=True, verbose_name=b'E-MAIL: When I get a question on my proposal'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='email_rfp_new',
            field=models.BooleanField(default=True, verbose_name=b'E-MAIL: When a new RFP that fits my services is posted'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='text_bid_change',
            field=models.BooleanField(default=True, verbose_name=b'TEXT: When a vendor posts a bid'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='text_bid_lose',
            field=models.BooleanField(default=True, verbose_name=b'TEXT: When my bid loses the contract'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='text_bid_win',
            field=models.BooleanField(default=True, verbose_name=b'TEXT: When my bid wins the contract'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='text_rfp_message',
            field=models.BooleanField(default=True, verbose_name=b'TEXT: When I get a question on my proposal'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='user',
            name='text_rfp_new',
            field=models.BooleanField(default=True, verbose_name=b'TEXT: When a new RFP that fits my services is posted'),
            preserve_default=True,
        ),
    ]
