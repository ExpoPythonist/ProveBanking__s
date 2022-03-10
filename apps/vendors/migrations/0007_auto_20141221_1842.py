# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def copy_categories_to_skills(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Vendor = apps.get_model("vendors", "Vendor")
    VendorCategories = apps.get_model("vendors", "VendorCategories")
    for vendor in Vendor.objects.all():
        VendorCategoriesList = list()
        for skill in vendor.categories.all():
            vendor_categ_obj = VendorCategories(skill=skill,
                                                vendor=vendor)
            VendorCategoriesList.append(vendor_categ_obj)

        VendorCategories.objects.bulk_create(VendorCategoriesList)


def copy_existing_roles(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Vendor = apps.get_model("vendors", "Vendor")
    VendorRoles = apps.get_model("vendors", "VendorRoles")
    VendorLocation = apps.get_model("vendors", "VendorLocation")

    for vendor in Vendor.objects.all():
        vendor_role_list = list()
        role_list = list()
        for obj in VendorLocation.objects.filter(vendor=vendor):
            role_list.extend(obj.roles.all())

        for role in set(role_list):
            vendor_role_obj = VendorRoles(role=role,
                                          vendor=vendor)
            vendor_role_list.append(vendor_role_obj)

        VendorRoles.objects.bulk_create(vendor_role_list)


def nothing(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('roles', '0001_initial'),
        ('categories', '0001_initial'),
        ('vendors', '0006_vendor_summary'),
    ]

    operations = [
        migrations.CreateModel(
            name='VendorCategories',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('allocation', models.PositiveSmallIntegerField(default=0, verbose_name='Role percentage')),
                ('skill', models.ForeignKey(to='categories.Category')),
                ('vendor', models.ForeignKey(to='vendors.Vendor')),
            ],
            options={
                'ordering': ('skill',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='VendorRoles',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('allocation', models.PositiveSmallIntegerField(default=0, verbose_name='Role percentage')),
                ('role', models.ForeignKey(to='roles.Role')),
                ('vendor', models.ForeignKey(to='vendors.Vendor')),
            ],
            options={
                'ordering': ('role',),
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='vendorroles',
            unique_together=set([('vendor', 'role')]),
        ),
        migrations.AlterUniqueTogether(
            name='vendorcategories',
            unique_together=set([('vendor', 'skill')]),
        ),
        migrations.AddField(
            model_name='vendor',
            name='roles',
            field=models.ManyToManyField(related_name=b'vendors', through='vendors.VendorRoles', to='roles.Role'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='vendor',
            name='skills',
            field=models.ManyToManyField(related_name=b'vendor', through='vendors.VendorCategories', to='categories.Category'),
            preserve_default=True,
        ),

        migrations.RunPython(copy_categories_to_skills,
                             nothing),
        migrations.RunPython(copy_existing_roles,
                             nothing),
        
        migrations.RemoveField(
            model_name='vendor',
            name='categories',
        ),

        migrations.RemoveField(
            model_name='vendor',
            name='skills',
        ),
        
        migrations.AddField(
            model_name='vendor',
            name='categories',
            field=models.ManyToManyField(related_name=b'vendors', through='vendors.VendorCategories', to='categories.Category'),
            preserve_default=True,
        ),

        migrations.RemoveField(
            model_name='vendorlocation',
            name='roles',
        ),

    ]
