import urlparse
from datetime import timedelta

from django.db import models, connection
from django.dispatch.dispatcher import receiver
from django.contrib.auth import get_user_model
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save
from django.conf import settings
from django.contrib.auth.models import Group
from django.utils.timezone import now
from django.contrib.sites.models import Site

from allauth.account.adapter import get_adapter
from allauth.utils import generate_unique_username
from djorm_pgarray.fields import SmallIntegerArrayField
from tenant_schemas.models import TenantMixin
from tenant_schemas.signals import post_schema_sync

from apps.features.models import get_all
from ACL.utils import (create_default_client_groups,
                       create_default_client_perms)
from vendors.mixins import KindMixin
from users.models import UserInvitation


class Customer(TenantMixin):
    RESERVED_DOMAINS = ('mail.proven.cc', 'static.proven.cc', 'blog.proven.cc', 'www.proven.cc')
    MONTHLY_PLAN_CHOICES = (
        ('monthly-10', '$10/month'),
        ('monthly-20', '$20/month'),
        ('monthly-50', '$50/month'),
        ('monthly-100', '$100/month'),
    )

    name = models.CharField(_('company name'), max_length=255)
    created_on = models.DateField(auto_now_add=True)
    email_domain = models.CharField(max_length=127, blank=True, null=True)
    email = models.EmailField(_('admin email address'))
    logo = models.ImageField(_('company logo'), null=True, blank=True, upload_to=settings.COMPANY_LOGO_IMAGE_FOLDER)
    background = models.ImageField(_('background'), null=True, blank=True, upload_to=settings.COMPANY_BACKGROUND_IMAGE_FOLDER)
    uniqueness = models.BooleanField(default=True)
    features = SmallIntegerArrayField(default=get_all(), dimension=1)

    direct_signup = models.BooleanField(default=False)
    is_public_instance = models.BooleanField(default=False)

    default_vendor_kind = models.PositiveSmallIntegerField(default=KindMixin.KIND_APPROVED, choices=KindMixin.KIND_CHOICES)

    description = models.TextField(blank=True)
    about_page_content = models.TextField(blank=True)
    about_page_video = models.URLField(_('YouTube video'), max_length=255, default='', blank=True)
    about_page_guide = models.FileField(_('How To Guide'), null=True, blank=True, upload_to=settings.COMPANY_LOGO_IMAGE_FOLDER)

    weight_market = models.FloatField(default=20, verbose_name='Market Score', help_text='Market cap and annual revenue')
    weight_web = models.FloatField(default=10, verbose_name='Web Score', help_text='Google Pagerank, Alexa Rank, Twitter Followers')
    weight_industry = models.FloatField(default=30, verbose_name='Industry Score', help_text='Contract billings among peers')
    weight_clients = models.FloatField(default=30, verbose_name='Client Score', help_text='Contract billings and durations weighed by client\'s annual revenue')
    weight_feedback = models.FloatField(default=10, verbose_name='Feedback Score', help_text='Feedback scores')

    monthly_plan = models.CharField(max_length=20, choices=MONTHLY_PLAN_CHOICES, default='monthly-50', help_text='How much to charge vendors of this community')
    invoice_limit = models.PositiveIntegerField(default=5, help_text='How many invoices can a vendor upload before charging')

    # default true, schema will be automatically created and synced when
    # it is saved
    auto_create_schema = True

    class Meta:
        unique_together = (('schema_name', 'uniqueness',),)

    def save(self, *args, **kwargs):
        if self.domain_url in self.RESERVED_DOMAINS:
            raise ValueError('%s is a reserved subdomain' % self.domain_url)
        self.uniqueness = True
        return super(Customer, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.name

    @property
    def is_public(self):
        return self.schema_name == settings.PUBLIC_SCHEMA_NAME

    def switch_to_tenant_db(self):
        connection.set_tenant(self)

    def switch_to_public_db(self):
        connection.set_schema_to_public()

    def get_full_url(self):
        return ''.join([settings.DEFAULT_HTTP_PROTOCOL, self.domain_url])

    def get_video_embed_url(self):
        o = urlparse.urlparse(self.about_page_video)
        if o.hostname in ('youtu.be', 'www.youtu.be'):
            return 'https://youtube.com/embed/%s' % o.path[1:]

        q = urlparse.parse_qs(o.query).get('v', [])
        if q:
            return 'https://youtube.com/embed/%s' % q[0]

    def domain_slug(self):
        return self.domain_url.split('.', 1)[0]


class CustomerConfig(models.Model):
    # TODO: add creations in post save for customers
    customer = models.OneToOneField(
        Customer,
        on_delete=models.CASCADE,
        primary_key=True
    )

    enable_periodic_rank_email = models.BooleanField(
        default=False
    )

    enable_clearbit = models.BooleanField(
        default=True
    )


class CustomerRequest(models.Model):
    name = models.CharField(_('Full name'), max_length=255)
    company = models.CharField(_('Company name'), max_length=255)
    email = models.EmailField(_('E-mail'), max_length=255)
    website = models.URLField(_('Website'), max_length=255, blank=True,
                              null=True)
    phone_number = models.CharField(_('Contact number'),
                                    max_length=255,
                                    null=True,
                                    blank=True)
    notes = models.TextField(_('Notes '), max_length=2047, default='',
                             null=True, blank=True)
    created_on = models.DateField(auto_now_add=True)

    def send_waitlist_email(self):
        get_adapter().send_mail('client/email/waitlist', self.email,
                                {'user': self})

    def __unicode__(self):
        return self.company


@receiver(post_save, sender=CustomerRequest)
def post_customer_invite_request_saved(sender, **kwargs):
    instance = kwargs['instance']
    if kwargs['created']:
        instance.send_waitlist_email()


@receiver(post_schema_sync, dispatch_uid='customers.Customer.post_schema_sync')
def create_superuser(sender, tenant=None, **kwargs):
    from django.core.management import call_command
    if tenant.schema_name == 'public':
        call_command('loaddata', 'med_social/fixtures/socialauth.json')
        return
    try:
        previous_schema = connection.schema_name
        connection.set_tenant(tenant)
        UserModel = get_user_model()

        # Populate default data for various apps
        call_command('loaddata', 'apps/reviews/fixtures/firsttime.json')
        call_command('loaddata', 'apps/categories/fixtures/firsttime.json')
        call_command('loaddata', 'apps/services/fixtures/firsttime.json')
        call_command('loaddata', 'apps/locations/fixtures/firsttime.json')
        call_command('loaddata', 'apps/roles/fixtures/firsttime.json')
        call_command('loaddata', 'apps/ACL/fixtures/firsttime.json')
        call_command('loaddata', 'apps/projects/fixtures/firsttime.json')
        call_command('loaddata', 'med_social/fixtures/socialauth.json')

        # Create default groups and perms
        create_default_client_groups()
        create_default_client_perms()

        # Create default user and sent out an invite
        username = generate_unique_username([tenant.email.split('@')[0]])
        # FIXME: make sure the guy is an admin
        password = UserModel.objects.make_random_password()
        admin = UserModel(username=username, email=tenant.email,
                          kind=UserModel.KIND_CLIENT)
        admin.set_password(password)
        admin.save()

        # Add client groups
        admin.groups.add(*Group.objects.filter(vendor=None))
        invitation, _ = UserInvitation.objects.get_or_create(
            receiver=admin, sender=None, defaults={
                'expires_at': now() + timedelta(days=7)
            })
        admin.send_customer_admin_welcome_email(
            tenant, password, invitation.get_absolute_url())
        # Update Site object
        site, created = Site.objects.get_or_create(pk=1)
        site.name = tenant.name + ' at Proven'
        site.domain = tenant.domain_url
        site.save()

    finally:
        schema = Customer.objects.get(schema_name=previous_schema)
        connection.set_tenant(schema)
