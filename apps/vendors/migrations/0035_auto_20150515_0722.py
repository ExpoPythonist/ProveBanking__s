# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0001_initial'),
        ('certs', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('categories', '0005_auto_20150504_0812'),
        ('vendors', '0034_merge'),
    ]

    operations = [
        migrations.CreateModel(
            name='CertVerification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url', models.URLField(default=b'', max_length=255, blank=True)),
                ('email', models.EmailField(max_length=75, null=True, blank=True)),
                ('email_msg', models.TextField(max_length=1000)),
                ('since', models.IntegerField(max_length=4, null=True, choices=[(2015, 2015), (2014, 2014), (2013, 2013), (2012, 2012), (2011, 2011), (2010, 2010), (2009, 2009), (2008, 2008), (2007, 2007), (2006, 2006), (2005, 2005), (2004, 2004), (2003, 2003), (2002, 2002), (2001, 2001), (2000, 2000), (1999, 1999), (1998, 1998), (1997, 1997), (1996, 1996), (1995, 1995), (1994, 1994), (1993, 1993), (1992, 1992), (1991, 1991), (1990, 1990), (1989, 1989), (1988, 1988), (1987, 1987), (1986, 1986), (1985, 1985), (1984, 1984), (1983, 1983), (1982, 1982), (1981, 1981), (1980, 1980), (1979, 1979), (1978, 1978), (1977, 1977), (1976, 1976), (1975, 1975), (1974, 1974), (1973, 1973), (1972, 1972), (1971, 1971), (1970, 1970), (1969, 1969), (1968, 1968), (1967, 1967), (1966, 1966), (1965, 1965), (1964, 1964), (1963, 1963), (1962, 1962), (1961, 1961), (1960, 1960), (1959, 1959), (1958, 1958), (1957, 1957), (1956, 1956), (1955, 1955), (1954, 1954), (1953, 1953), (1952, 1952), (1951, 1951), (1950, 1950), (1949, 1949), (1948, 1948), (1947, 1947), (1946, 1946), (1945, 1945), (1944, 1944), (1943, 1943), (1942, 1942), (1941, 1941), (1940, 1940), (1939, 1939), (1938, 1938), (1937, 1937), (1936, 1936), (1935, 1935), (1934, 1934), (1933, 1933), (1932, 1932), (1931, 1931), (1930, 1930), (1929, 1929), (1928, 1928), (1927, 1927), (1926, 1926), (1925, 1925), (1924, 1924), (1923, 1923), (1922, 1922), (1921, 1921), (1920, 1920), (1919, 1919), (1918, 1918), (1917, 1917), (1916, 1916), (1915, 1915), (1914, 1914), (1913, 1913), (1912, 1912), (1911, 1911), (1910, 1910), (1909, 1909), (1908, 1908), (1907, 1907), (1906, 1906), (1905, 1905), (1904, 1904), (1903, 1903), (1902, 1902), (1901, 1901), (1900, 1900)])),
                ('token', models.CharField(max_length=40)),
                ('is_fulfilled', models.BooleanField(default=False)),
                ('is_verified', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('cert', models.ForeignKey(to='certs.Cert')),
                ('created_by', models.ForeignKey(related_name='cert_verifications', to=settings.AUTH_USER_MODEL)),
                ('vendor', models.ForeignKey(related_name='cert_verifications', to='vendors.Vendor')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ClientReference',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(max_length=75, null=True)),
                ('email_msg', models.TextField(max_length=1000)),
                ('alt_name', models.CharField(max_length=255, null=True)),
                ('use_alt_name', models.BooleanField(default=False)),
                ('billing', models.PositiveSmallIntegerField(blank=True, null=True, choices=[(1, b'$0 - $10K'), (2, b'$10 - $50K'), (3, b'$50 - $100K'), (4, b'$100K - $500k'), (5, b'$500K - $1M'), (6, b'$1M - $5M'), (7, b'$5M - $10M'), (8, b'$10M+')])),
                ('billing_private', models.BooleanField(default=True)),
                ('duration', models.PositiveSmallIntegerField(default=1, choices=[(1, b'less than 1 year'), (2, b'2 - 3 years'), (3, b'3 - 5 years'), (4, b'5 - 10 years'), (5, b'10+ years')])),
                ('duration_private', models.BooleanField(default=False)),
                ('has_ended', models.BooleanField(default=False)),
                ('rating', models.DecimalField(null=True, max_digits=2, decimal_places=1)),
                ('review', models.TextField(null=True, blank=True)),
                ('review_anonymous', models.BooleanField(default=False)),
                ('role', models.CharField(max_length=255, null=True, blank=True)),
                ('full_name', models.CharField(max_length=255, null=True, blank=True)),
                ('token', models.CharField(max_length=40)),
                ('is_fulfilled', models.BooleanField(default=False)),
                ('is_verified', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('last_sent', models.DateTimeField(auto_now_add=True)),
                ('is_enabled', models.BooleanField(default=False)),
                ('client', models.ForeignKey(related_name='references', to='clients.Client')),
                ('created_by', models.ForeignKey(related_name='client_references', to=settings.AUTH_USER_MODEL)),
                ('vendor', models.ForeignKey(related_name='client_references', to='vendors.Vendor')),
            ],
            options={
                'ordering': ('-is_verified', 'rating'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='VendorIndustry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('allocation', models.PositiveSmallIntegerField(default=1, verbose_name='Industry percentage')),
                ('industry', models.ForeignKey(to='categories.Category')),
                ('vendor', models.ForeignKey(related_name='vendor_industries', to='vendors.Vendor')),
            ],
            options={
                'ordering': ('industry',),
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='vendorindustry',
            unique_together=set([('vendor', 'industry')]),
        ),
        migrations.CreateModel(
            name='VendorSearchTerm',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('vendors.vendor',),
        ),
        migrations.AddField(
            model_name='vendor',
            name='certs',
            field=models.ManyToManyField(related_name='vendors', through='vendors.CertVerification', to='certs.Cert'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='vendor',
            name='clients',
            field=models.ManyToManyField(related_name='vendors', through='vendors.ClientReference', to='clients.Client'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='vendor',
            name='industries_served',
            field=models.ManyToManyField(related_name='vendor_industry', through='vendors.VendorIndustry', to='categories.Category'),
            preserve_default=True,
        ),
    ]
