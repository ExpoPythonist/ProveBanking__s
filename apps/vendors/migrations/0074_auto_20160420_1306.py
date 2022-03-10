# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0073_auto_20160411_1705'),
    ]

    operations = [
        migrations.AddField(
            model_name='certverification',
            name='cert_type',
            field=models.IntegerField(default=1, choices=[(1, 'Certification'), (2, 'Insurance')]),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='certverification',
            name='expiry_date',
            field=models.DateTimeField(null=True, blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='invoice',
            name='invoice',
            field=models.FileField(upload_to='client-invoices', null=True, verbose_name='Proof', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='invoice',
            name='invoice_amount',
            field=models.DecimalField(null=True, verbose_name='Contract Amount', max_digits=20, decimal_places=2),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='invoice',
            name='invoice_duration',
            field=models.IntegerField(null=True, verbose_name='Contract Duration', choices=[(1, '1 day+'), (7, '1 week+'), (30, '1 month+'), (90, '3 months+'), (180, '6 months+'), (360, '1 year+'), (540, '1.5 years+'), (720, '2 years+'), (1080, '3 years+'), (1440, '4 years+'), (1800, '5 years+')]),
            preserve_default=True,
        ),
    ]
