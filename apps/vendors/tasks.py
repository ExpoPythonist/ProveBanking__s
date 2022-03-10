import urllib
import os
import clearbit
import json
import time
from datetime import timedelta, date
from urlparse import urlparse
from dateutil import parser, relativedelta
from collections import OrderedDict
from logging import getLogger

import requests
from django.core.files import File
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.contenttypes.models import ContentType
from django.db import connection
from django.db.models import Avg, Q
from django.contrib.auth import get_user_model
from django.utils.timezone import now

from allauth.utils import generate_unique_username
from annoying.functions import get_object_or_None
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from celery.task import task
from notifications.signals import notify
from post_office import mail
from tenant_schemas.utils import tenant_context, get_tenant_model

from med_social.utils import slugify

from customers.models import Customer, CustomerConfig
from categories.models import Category
from features import models as features
from locations.models import Location
from metrics.models import Metric
from users.models import UserInvitation, User
from users.tasks import user_invite

from .models import (Vendor, VendorScoreAggregate, PortfolioItem, ClientReference, CertVerification, ProcurementContact,
                     VendorCategories, VendorLocation, VendorCustomKind, VendorWhois, InsuranceVerification)

from .emails.views import (ReviewRequestEmail, ClientReferenceEmail,
                           CertVerificationEmail, ClientRespondedEmail, ProcurementNotifyEmail, ProcurementAddedEmail,
                           InsuranceVerificationEmail)


logger = getLogger(__name__)


@task
def vendor_invite(tenant_id, invite_id):
    tenant = get_object_or_None(Customer, id=tenant_id)
    if not tenant:
        return

    with tenant_context(tenant):
        invite = get_object_or_None(UserInvitation, id=invite_id)
        if not invite:
            return
        url = ''.join([settings.DEFAULT_HTTP_PROTOCOL, tenant.domain_url])
        mail.send(invite.receiver.email, sender=invite.sender.get_sender_line(), template='Vendor Invite', context={
            'current_tenant': tenant,
            'direct_url': ''.join([url, invite.get_absolute_url()]),
            'receiver': invite.receiver,
            'sender': invite.sender,
            'reset_password_url': reverse('account_change_password'),
        })


@task
def vendor_application_notif(tenant_id, vendor_id):
    tenant = get_object_or_None(Customer, id=tenant_id)
    if not tenant:
        return

    with tenant_context(tenant):
        vendor = get_object_or_None(Vendor, id=vendor_id)
        if not vendor:
            return

        if vendor.client_contact:
            notify.send(
                sender=vendor,
                verb='submitted a supplier application',
                target=None,
                action_object=vendor,
                recipient=vendor.client_contact
            )


@task
def aggregate_metric_for_vendor(tenant_id):
    from metrics.tasks import aggregate_metric_for_object
    tenant = get_object_or_None(Customer, id=tenant_id)
    if not tenant:
        return

    with tenant_context(tenant):
        for vendor in Vendor.objects.all():
            content_type = ContentType.objects.get_for_model(Vendor)
            aggregate_metric_for_object.delay(tenant_id=tenant_id,
                                              content_type=content_type.id,
                                              object_id=vendor.id,
                                              kind=Metric.RESPONSE_TIME)
            aggregate_metric_for_object.delay(tenant_id=tenant_id,
                                              content_type=content_type.id,
                                              object_id=vendor.id,
                                              kind=Metric.ACCEPTANCE_RATE)
            aggregate_metric_for_object.delay(tenant_id=tenant_id,
                                              content_type=content_type.id,
                                              object_id=vendor.id,
                                              kind=Metric.USER_RATING)


@task
def vendor_user_rating(tenant_id):
    from metrics.tasks import create_metric
    tenant = get_object_or_None(get_tenant_model(), id=tenant_id)
    if not tenant:
        return
    with tenant_context(tenant):
        for vendor in Vendor.objects.all():
            objects = User.objects.filter(vendor=vendor)
            content_type = ContentType\
                .objects.get_for_model(User)
            target_type = ContentType\
                .objects.get_for_model(Vendor)
            for obj in objects:
                if obj.avg_score:
                    create_metric.delay(tenant_id=tenant.id,
                                        content_type=content_type.id,
                                        object_id=obj.id,
                                        target_type=target_type.id,
                                        target_id=vendor.id,
                                        kind=Metric.USER_RATING,
                                        score=obj.avg_score)


@task
def vendor_aggregate_ratings(tenant_id):
    tenant = get_object_or_None(get_tenant_model(), id=tenant_id)
    if not tenant:
        return
    with tenant_context(tenant):
        for vendor in Vendor.objects.all():
            vendor_aggregate, _ = VendorScoreAggregate\
                .objects.get_or_create(vendor=vendor)

            vendor_aggregate.response_time = vendor.metric_aggregate\
                .filter(kind=Metric.RESPONSE_TIME)\
                .aggregate(Avg('score'))['score__avg']
            vendor_aggregate.acceptance_rate = vendor.metric_aggregate\
                .filter(kind=Metric.ACCEPTANCE_RATE)\
                .aggregate(Avg('score'))['score__avg']
            vendor_aggregate.user_rating = vendor.metric_aggregate\
                .filter(kind=Metric.USER_RATING)\
                .aggregate(Avg('score'))['score__avg']

            vendor_aggregate.save()


@periodic_task(run_every=(crontab(0, 8, day_of_month='1')), ignore_result=True)
def vendor_aggregate_schedule():
    for tenant in get_tenant_model().objects.all():
        vendor_aggregate_ratings.delay(tenant_id=tenant.id)


@task
def request_review_email(tenant_id, instance_id):
    tenant = get_object_or_None(Customer, id=tenant_id)
    if not tenant:
        return

    with tenant_context(tenant):
        portfolio_item = get_object_or_None(PortfolioItem, id=instance_id)
        if not portfolio_item:
            return

        for recipient in portfolio_item.owners.all():
            ReviewRequestEmail(recipient=recipient,
                               portfolio_item=portfolio_item).send()


@task
def user_invite_portfolio(tenant_id, portfolio_id, sender_id, email, kind):
    tenant = get_object_or_None(get_tenant_model(), id=tenant_id)
    if not tenant:
        return

    with tenant_context(tenant):
        password = get_user_model().objects.make_random_password()
        username = generate_unique_username(email)
        tenant = connection.get_tenant()

        sender = get_object_or_None(get_user_model(), id=sender_id)
        if not sender:
            return

        portfolio_item = get_object_or_None(PortfolioItem, id=portfolio_id)
        if not portfolio_item:
            return

        if not get_user_model().objects.filter(email=email).first():
            user = get_user_model().objects.create(email=email,
                                                   username=username)
            user.kind = kind
            user.set_password(password)
            user.save()

            portfolio_item.owners.add(user)
            expires_at = now() + timedelta(days=7)
            user_invitation, _ = user.invitations.get_or_create(
                sender=sender,
                receiver=user,
                defaults={'expires_at': expires_at})

            user_invitation.expires_at = expires_at
            user_invitation.save()
            user_invite.delay(tenant_id=tenant.id,
                              invite_id=user_invitation.id,
                              password=password)


@task
def client_add(client_ref, tenant_id):
    tenant = get_object_or_None(Customer, id=tenant_id)
    if not tenant:
        return
    with tenant_context(tenant):
        client = get_object_or_None(ClientReference, id=client_ref)
        if not client:
            return
        if not client.email:
            return
        ClientReferenceEmail(client).send()


@task
def cert_verification(cert_id, tenant_id):
    tenant = get_object_or_None(Customer, id=tenant_id)
    if not tenant:
        return
    with tenant_context(tenant):
        cert = get_object_or_None(CertVerification, id=cert_id)
        if not cert:
            return
        if cert.cert.kind == cert.cert.KIND_PARTNER:
            try:
                recipients = (cert.cert.client.users.earliest('date_joined').email,)
            except get_user_model().DoesNotExist:
                recipients = map(lambda x: x[1], settings.ADMINS)
            CertVerificationEmail(cert, recipients).send()
        elif cert.email:
            CertVerificationEmail(cert, (cert.email,)).send()


@task
def insurance_verification(insurance_id, tenant_id):
    tenant = get_object_or_None(Customer, id=tenant_id)
    if not tenant:
        return
    with tenant_context(tenant):
        insurance = get_object_or_None(InsuranceVerification, id=insurance_id)
        if not insurance:
            return
        if insurance.email:
            InsuranceVerificationEmail(insurance, (insurance.email,)).send()


@task
def client_responded(client_ref, tenant_id):
    tenant = get_object_or_None(Customer, id=tenant_id)
    if not tenant:
        return
    with tenant_context(tenant):
        client = get_object_or_None(ClientReference, id=client_ref)
        if not client:
            return
        ClientRespondedEmail(client).send()


@task
def populate_clearbit_data(tenant_id, instance_id):
    tenant = get_object_or_None(Customer, id=tenant_id)
    if not tenant:
        return

    with tenant_context(tenant):
        instance = get_object_or_None(Vendor, id=instance_id)
        if not instance:
            return

        clearbit.key = settings.CLEARBIT_KEY
        domain = urlparse(instance.website).netloc
        company = clearbit.Company.find(domain=domain, stream=True)
        if company['description']:
            instance.summary = company['description'][:490]
        for tag in company['tags']:
            skill, _ = Category.objects.get_or_create(slug=slugify(tag), kind=Category.KIND_SKILL, defaults={'name': tag})

            VendorCategories.objects.get_or_create(skill=skill,
                                                   vendor=instance)
        logo_url = company['logo']
        if logo_url:
            if logo_url.startswith('https'):
                logo_url = logo_url.replace('https', 'http')

            result = urllib.urlretrieve(logo_url)
            instance.logo.save(
                os.path.basename(logo_url),
                File(open(result[0]))
            )
        if company['twitter'].get('handle'):
            instance.twitter = company['twitter'].get('handle')
            instance.meta['twitter_followers'] = company['twitter'].get('followers')

        if company.get('angellist', {}).get('handle'):
            instance.meta['angellist'] = company['angellist'].get('handle')
            instance.meta['angellist_followers'] = company['angellist'].get('followers')

        if company['facebook'].get('handle'):
            instance.facebook = company['facebook'].get('handle')
        if company['linkedin'].get('handle'):
            instance.linkedin = company['linkedin'].get('handle')

        if company['location']:
            instance.address = company['location']
        if company['geo'].get('country'):
            location = Location.objects.filter(city__iexact=company['geo'].get('country')).first()
            if location:
                VendorLocation.objects.get_or_create(location=location,
                                                     vendor=instance)

        instance.save()


@task(time_limit=60 * 10)
def populate_vendors_clearbit_data():
    """
    Populate Clearbit data for vendors on specified customers.
    """
    clearbit.key = settings.CLEARBIT_KEY
    for tenant in Customer.objects.select_related('customerconfig'):
        with tenant_context(tenant):
            try:
                config = tenant.customerconfig
            except CustomerConfig.DoesNotExist:
                logger.warning("Config don't exists for tenant %s", tenant.id)
                continue

            if config and config.enable_clearbit:
                vendors = Vendor.objects.filter(sync_clearbit=False).order_by('-proven_score')[:200]
                for vendor in vendors:
                    try:
                        if vendor.email:
                            response = clearbit.Enrichment.find(email=vendor.email, stream=True)
                            company_data = response and response['company']
                        elif vendor.website:
                            response = clearbit.Enrichment.find(domain=vendor.website, stream=True)
                            company_data = response and dict(response)
                        else:
                            company_data = dict()

                        if not company_data:
                            logger.warning('No Clearbit data for %s', vendor)
                            vendor.sync_clearbit = True
                            vendor.save(update_fields=['modified_on', 'sync_clearbit'])
                            continue

                        twitter = company_data.get('twitter', {}).get('handle') or ''
                        facebook = company_data.get('facebook', {}).get('handle') or ''
                        linkedin = company_data.get('facebook', {}).get('handle') or ''
                        phone = company_data.get('phone')
                        address = company_data.get('location', '') or ''

                        vendor.twitter = twitter
                        vendor.facebook = facebook
                        vendor.linkedin = linkedin
                        vendor.address = address
                        if phone:
                            vendor.phone = phone
                        vendor.sync_clearbit = True

                        vendor.save(update_fields=['twitter', 'facebook', 'linkedin', 'address',
                                                   'phone', 'sync_clearbit', 'modified_on'])
                    except requests.HTTPError as e:
                        logger.warning('HTTPError: %s', str(e))
                    except Exception as e:
                        logger.exception(e)
                    finally:
                        time.sleep(10)


@task
def calculate_rank(tenant_id, vendor_id):
    tenant = get_object_or_None(Customer, id=tenant_id)
    if not tenant:
        return

    with tenant_context(tenant):
        vendor = get_object_or_None(Vendor, id=vendor_id)
        if not vendor:
            return
        category = vendor.get_primary_service()
        if category:
            category_objects = VendorCustomKind.objects.filter(primary=True, category=category.category).order_by('-vendor__proven_score', 'vendor__id')
            if category_objects:
                new_top = None
                old_top = None
                for count, obj in enumerate(category_objects):
                    orig_rank = obj.rank
                    obj.rank = count + 1
                    obj.save()

                    if obj.rank != orig_rank:
                        if orig_rank == 1:
                            old_top = obj.vendor
                        elif obj.rank == 1:
                            new_top = obj.vendor

                if features.proven_score.is_enabled() and new_top:
                    category = category.category
                    customs = VendorCustomKind.objects.filter(category=category, primary=True).order_by('-vendor__proven_score')
                    for receiver in new_top.users.all():
                        mail.send(receiver.email, template='No. 1 Periodic / Instant', context={
                            'community': tenant,
                            'community_url': tenant.get_full_url(),
                            'receiver': receiver,
                            'category': category,
                            'customs': customs,
                            'vendor': new_top,
                        })

                    if old_top:
                        for receiver in old_top.users.all():
                            mail.send(receiver.email, template='Out of No. 1', context={
                                'community': tenant,
                                'community_url': tenant.get_full_url(),
                                'receiver': receiver,
                                'category': category,
                                'customs': customs,
                                'competitor': new_top,
                                'category': category,
                                'vendor': old_top,
                            })


@task
def calculate_rank_by_categ(tenant_id, category_id):
    tenant = get_object_or_None(Customer, id=tenant_id)
    if not tenant:
        return

    with tenant_context(tenant):
        category = get_object_or_None(Category, id=category_id)
        if category:
            category_objects = VendorCustomKind.objects.filter(primary=True, category=category).order_by('-vendor__proven_score', 'vendor__id')
            if category_objects:
                new_top = None
                old_top = None
                for count, obj in enumerate(category_objects):
                    orig_rank = obj.rank
                    obj.rank = count + 1
                    obj.save()

                    if obj.rank != orig_rank:
                        if orig_rank == 1:
                            old_top = obj.vendor
                        elif obj.rank == 1:
                            new_top = obj.vendor

                if features.proven_score.is_enabled() and new_top:
                    category = category.category
                    customs = VendorCustomKind.objects.filter(category=category,
                                                              primary=True).order_by('-vendor__proven_score')
                    for receiver in new_top.users.all():
                        mail.send(receiver.email, template='No. 1 Periodic / Instant', context={
                            'community': tenant,
                            'community_url': tenant.get_full_url(),
                            'receiver': receiver,
                            'category': category,
                            'customs': customs,
                            'vendor': new_top,
                        })

                    if old_top:
                        for receiver in old_top.users.all():
                            mail.send(receiver.email, template='Out of No. 1', context={
                                'community': tenant,
                                'community_url': tenant.get_full_url(),
                                'receiver': receiver,
                                'category': category,
                                'customs': customs,
                                'competitor': new_top,
                                'category': category,
                                'vendor': old_top,
                            })


def procurement_assigned_notify(tenant_id, instance_id):
    tenant = get_object_or_None(Customer, id=tenant_id)
    if not tenant:
        return

    with tenant_context(tenant):
        custom_category = get_object_or_None(VendorCustomKind, id=instance_id)
        if not custom_category:
            return
        vendor = custom_category.vendor

        if not vendor.procurement_contacts.exists():
            procurement = ProcurementContact.objects.filter(categories=custom_category.category)

            for obj in procurement:
                vendor.procurement_contacts.add(obj)
                ProcurementAddedEmail(recipient=obj.user,
                                      vendor=vendor
                                      ).send()


@task
def populate_whois_data(tenant_id, instance_id):
    tenant = get_object_or_None(Customer, id=tenant_id)
    if not tenant:
        return

    with tenant_context(tenant):
        vendor = get_object_or_None(Vendor, id=instance_id)
        if not vendor:
            return

        result_json = {}
        domain = urlparse(vendor.website).netloc
        params = {'domain': domain}

        headers = {"Accept": "application/json",
                   "Authorization": "Token token=ebea1c4678641d215b3784b6c461acc4"}

        result = requests.get('https://jsonwhois.com/api/v1/whois',
                              headers=headers,
                              params=params)
        result_json['whois'] = json.loads(result.text)
        whois_obj, _ = VendorWhois.objects.get_or_create(vendor=vendor)
        if result_json['whois']:
            if result_json['whois'].get('domain'):
                whois_obj.domain = result_json['whois'].get('domain')

            if result_json['whois'].get('created_on') and result_json['whois'].get('expires_on'):
                date_created = parser.parse(result_json['whois'].get('created_on'))
                date_expire = parser.parse(result_json['whois'].get('expires_on'))
                whois_obj.created_on = date_created
                whois_obj.expires_on = date_expire

            if result_json['whois'].get('registrant_contacts'):
                whois_obj.registrant = result_json['whois'].get('registrant_contacts')[0].get('name')
                whois_obj.email = result_json['whois'].get('registrant_contacts')[0].get('email')
                whois_obj.address = result_json['whois'].get('registrant_contacts')[0].get('address')
                whois_obj.phone = result_json['whois'].get('registrant_contacts')[0].get('phone')

        clearbit.key = settings.CLEARBIT_KEY
        company = clearbit.Company.find(domain=domain, stream=True)
        if not whois_obj.metrics:
            whois_obj.metrics = {}
        if company:
            if company.get('metrics'):
                whois_obj.metrics['alexaGlobalRank'] = company['metrics'].get('alexaGlobalRank','')
                whois_obj.metrics['employees'] = company['metrics'].get('employees','')
                whois_obj.metrics['googleRank'] = company['metrics'].get('googleRank','')
                whois_obj.metrics['raised'] = company['metrics'].get('raised','')

            if not whois_obj.social_handles:
                whois_obj.social_handles = {}

            if company['facebook']:
                whois_obj.social_handles['facebook'] = company['facebook'].get('handle', "")

            if company['twitter']:
                whois_obj.social_handles['twitter'] = company['twitter'].get('handle', "")

            if company['linkedin']:
                whois_obj.social_handles['linkedin'] = company['linkedin'].get('handle', "")

        whois_obj.save()


@task
def glassdoor_check(tenant_id, instance_id):
    tenant = get_object_or_None(Customer, id=tenant_id)
    if not tenant:
        return

    with tenant_context(tenant):
        vendor = get_object_or_None(Vendor, id=instance_id)
        if not vendor:
            return
        response_json = {}

        #needs glassdoor api credentials
        params_gd = OrderedDict({
            "v": "1",
            "format": "json",
            "t.p": "",
            "t.k": "",
            "action": "employers",
            "q": vendor.name,
            # programmatically get the IP of the machine
            "useragent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36"
        })

        # construct the URL from parameters
        basepath_gd = 'http://api.glassdoor.com/api/api.htm'

        # request the API
        response_gd = requests.get(basepath_gd,
                                   params=params_gd,
                                   headers={
                                       "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36"
                                   })

        response_json = json.loads(response_gd.text)
        if response_json.get('response') and response_json.get('response').get('employers'):
            if response_json.get('response').get('employers')[0].get('name'):
                if response_json.get('response').get('employers')[0].get('name').lower() == vendor.name:
                    vendor.verifications['glassdoor'] = response_json.get('response').get('employers')[0]
                    vendor.save()


@periodic_task(run_every=(crontab(0, 16, day_of_month=1)), ignore_result=True)
def send_weekly_rank_emails_admins():
    for tenant in get_tenant_model().objects.all():
        with tenant_context(tenant):
            if features.proven_score.is_enabled():
                categories = Category.objects.filter(custom_kind_obj__primary=True,
                                                     vendors_custom__isnull=False).distinct()
                for receiver in User.objects.filter(procurement_contacts__isnull=False):
                    mail.send(receiver.email, template='Weekly Community Manager', context={
                        'community': tenant,
                        'community_url': tenant.get_full_url(),
                        'receiver': receiver,
                        'categories': categories,
                    })


@periodic_task(run_every=(crontab(0, 16, day_of_month=1)), ignore_result=True)
def send_weekly_rank_emails_vendors():
    for tenant in get_tenant_model().objects.all():
        with tenant_context(tenant):
            if features.proven_score.is_enabled():
                categories = Category.objects.filter(custom_kind_obj__primary=True, vendors_custom__isnull=False).distinct()

                for category in categories:
                    # TODO: add open_for_business filtering
                    customs = VendorCustomKind.objects.filter(category=category, primary=True).order_by('-vendor__proven_score')
                    top_vendor = customs[0].vendor
                    for receiver in top_vendor.users.all():
                        if receiver.email:
                            mail.send(receiver.email, template='No. 1 Periodic / Instant', context={
                                'community': tenant,
                                'community_url': tenant.get_full_url(),
                                'receiver': receiver,
                                'category': category,
                                'customs': customs,
                                'vendor': top_vendor,
                            })

                    for rank, custom in enumerate(customs[1:], 2):
                        vendor = custom.vendor
                        for receiver in vendor.users.all():
                            if receiver.email:
                                mail.send(receiver.email, template='No. 2+ Periodic', context={
                                    'community': tenant,
                                    'community_url': tenant.get_full_url(),
                                    'receiver': receiver,
                                    'category': category,
                                    'customs': customs,
                                    'vendor': vendor,
                                    'rank': rank,
                                })


@periodic_task(run_every=(crontab(0, 15)), ignore_result=True)
def send_insurance_expiry_reminders():
    today = date.today()
    next_week = today + relativedelta.relativedelta(weeks=1)
    next_month = today + relativedelta.relativedelta(months=1)
    for tenant in get_tenant_model().objects.all():
        with tenant_context(tenant):
            for vendor in Vendor.objects.filter(
                Q(insurance_verifications__expiry_date=next_month) |
                Q(insurance_verifications__expiry_date=next_week)
            ).distinct():
                insurance = vendor.insurance_verifications.filter(
                    Q(expiry_date=next_month) | Q(expiry_date=next_week)
                ).order_by('expiry_date').first()
                for receiver in vendor.users.all():
                    mail.send(receiver.email, template='Insurance Expiration Reminder', context={
                        'community': tenant,
                        'receiver': receiver,
                        'insurance': insurance,
                        'rfp_enabled': False,
                        'rfp_template_link': '',
                    })
