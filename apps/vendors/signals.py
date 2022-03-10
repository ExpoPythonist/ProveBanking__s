from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import connection
from django.dispatch.dispatcher import receiver
from django.db.models.signals import post_save, post_delete
from django.utils.timezone import now
from django.contrib.contenttypes.models import ContentType

from annoying.functions import get_object_or_None
from allauth.utils import generate_unique_username
from med_social.utils import track_event

from ACL.utils import create_default_vendor_perms
from activity.models import Action
from users.models import User

from .models import (Vendor, PortfolioItem, ClientReference, CertVerification, VendorCustomKind,
                     Score, VendorWhois, InsuranceVerification)
from .tasks import (vendor_invite, request_review_email, client_responded, client_add,
                    cert_verification, populate_clearbit_data, calculate_rank_by_categ,
                    procurement_assigned_notify, populate_whois_data, glassdoor_check, insurance_verification)


@receiver(post_save, sender=PortfolioItem, dispatch_uid='reviews.portfolioitem.post_save')
def send_portfolio_save(sender, **kwargs):
    instance = kwargs.get('instance')
    created = kwargs.get('created')
    tenant = connection.get_tenant()
    if created:
        request_review_email.delay(tenant.id, instance.id)
    instance.score_update()


@receiver(post_save, sender=ClientReference, dispatch_uid='vendors.ClientReference.post_save')
def post_save_client(sender, **kwargs):
    instance = kwargs.get('instance')
    tenant = connection.get_tenant()
    if instance.tracker.has_changed('is_fulfilled') and instance.is_fulfilled and not instance.invoice_verification:
        client_responded.delay(instance.id, tenant.id)
    if instance.email and not instance.is_fulfilled and not instance.invoice_verification:
        client_add.apply_async(args=(instance.id, tenant.id))
    instance.score_update()


@receiver(post_save, sender=CertVerification, dispatch_uid='vendors.CertVerification.post_save')
def post_save_cert(sender, **kwargs):
    created = kwargs.get('created')
    instance = kwargs.get('instance')
    tenant = connection.get_tenant()

    if created:
        cert_verification.delay(instance.id, tenant.id)


@receiver(post_save, sender=InsuranceVerification, dispatch_uid='vendors.InsuranceVerification.post_save')
def post_save_insurance(sender, **kwargs):
    created = kwargs.get('created')
    instance = kwargs.get('instance')
    tenant = connection.get_tenant()

    if created:
        insurance_verification.delay(instance.id, tenant.id)


@receiver(post_save, sender=Vendor, dispatch_uid='vendors.Vendor.post_save')
def post_save_vendor(sender, **kwargs):
    created = kwargs.get('created')
    instance = kwargs.get('instance')
    tenant = connection.get_tenant()

    if not created:
        modified = instance.tracker.changed().get('modified_on')
        delta = timedelta(minutes=60)
        wait_time = now() - delta
        if modified and modified < wait_time:
            # vendor_procurement_notify.delay(instance.id, tenant.id)
            # TODO: delete this logic
            pass

        # if instance.tracker.has_changed('kind') and\
        #         instance.tracker.previous('kind') == instance.KIND_PROSPECTIVE:
        #     v = Vendor.objects.get(id=instance.id)
        #     v.has_onboarded = True
        #     v.save()
    else:
        VendorWhois.objects.get_or_create(vendor=instance)
        track_event(
            'Vendor:created',
            {
                'vendor_id': instance.id,
                'vendor': instance.name,
            },
        )

    if instance.tracker.has_changed('website') and instance.website:
        populate_clearbit_data.delay(tenant_id=tenant.id,
                                     instance_id=instance.id)
        populate_whois_data.delay(tenant_id=tenant.id,
                                  instance_id=instance.id)
        glassdoor_check.delay(tenant_id=tenant.id,
                              instance_id=instance.id)

    instance.score_update()

    if instance.tracker.has_changed('kind') and not tenant.is_public_instance:
        score_obj_kind, _ = Score.objects.get_or_create(vendor=instance,
                                                        kind=Score.KIND_VENDOR_KIND)
        score_obj_kind.score = instance.KIND_SCORES.get(instance.kind, 0)
        score_obj_kind.save()


@receiver(post_save, sender=VendorCustomKind, dispatch_uid='vendors.vendorcustomkind.post_save')
def send_review_request(sender, **kwargs):
    instance = kwargs.get('instance')
    created = kwargs.get('created')
    tenant = connection.get_tenant()
    primary = instance.tracker.changed().get('primary')
    if created:
        if instance.primary:
            calculate_rank_by_categ.delay(tenant.id, instance.category.id)
        if VendorCustomKind.objects.filter(vendor=instance.vendor).count() == 1:
            procurement_assigned_notify(tenant.id, instance.id)

    elif instance.tracker.has_changed('primary') and primary != None:
        calculate_rank_by_categ.delay(tenant.id, instance.category.id)


@receiver(post_delete, sender=VendorCustomKind, dispatch_uid='vendors.vendorcustomkind.post_delete')
def custom(sender, **kwargs):
    instance = kwargs.get('instance')
    tenant = connection.get_tenant()
    if instance.primary:
        calculate_rank_by_categ.delay(tenant.id, instance.category.id)


@receiver(post_delete, sender=ClientReference, dispatch_uid='vendors.clientreference.post_delete')
def clientreference_delete(sender, **kwargs):
    instance = kwargs.get('instance')
    instance.vendor.save()

from djstripe.signals import subscription_made


@receiver(subscription_made)
def set_vendor_premium(sender, **kwargs):
    user = sender.subscriber
    user.vendor.premium = True
    user.vendor.save()
