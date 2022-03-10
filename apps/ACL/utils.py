from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType

from .defaults import CLIENT_GROUPS


def create_default_client_groups():
    for name, display_name, kind in CLIENT_GROUPS:
        group, created = Group.objects.get_or_create(
            kind=kind, vendor=None, name=name, defaults={'display_name': display_name})

        if not created:
            group.display_name = display_name
            group.save()


def create_default_client_perms():
    for contenttype in ContentType.objects.all():
        create_default_client_perms_for_content_type(contenttype)


def create_default_client_perms_for_content_type(content_type):
    model = content_type.model_class()
    perms = getattr(model, 'PERMISSIONS', tuple())

    client_admin = Group.objects.get(kind=Group.DEFAULT_ADMIN, vendor=None)
    client_user = Group.objects.get(kind=Group.DEFAULT_USER, vendor=None)

    for codename, name, kind, admin_only in perms:
        if kind == Permission.VENDOR:
            continue

        perm, created = Permission.objects.get_or_create(
            codename=codename, content_type=content_type, defaults={'name': name, 'visibility': kind})
        if not created:
            perm.name = name
            perm.visibility = kind
            perm.save()

        if admin_only:
            perm.group_set.add(client_admin)
        else:
            perm.group_set.add(*[client_admin, client_user])


def create_default_vendor_perms(vendor):
    for contenttype in ContentType.objects.all():
        create_default_vendor_perms_for_content_type(contenttype, vendor)


def create_default_vendor_perms_for_content_type(content_type, vendor):
    model = content_type.model_class()
    perms = getattr(model, 'PERMISSIONS', tuple())

    vendor_admin = vendor.get_admins_group()
    vendor_user = vendor.get_users_group()

    for codename, name, kind, admin_only in perms:
        if kind == Permission.CLIENT:
            continue

        perm, created = Permission.objects.get_or_create(
            codename=codename, content_type=content_type, defaults={'name': name, 'visibility': kind})
        if not created:
            perm.name = name
            perm.visibility = kind
            perm.save()

        if admin_only:
            perm.group_set.add(vendor_admin)
        else:
            perm.group_set.add(*[vendor_admin, vendor_user])
