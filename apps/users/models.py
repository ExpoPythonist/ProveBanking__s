import os
import datetime
import hashlib
import hmac
import logging
import re
import uuid
from collections import namedtuple
from datetime import date, timedelta

from django.contrib.sites.models import Site
from django.core import validators
from django.core.urlresolvers import reverse
from django.conf import settings
from django.dispatch import receiver
from django.db import models, connection
from django.db.models import Q, Avg
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_init, post_save
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import UserManager, Permission
from django.contrib.contenttypes import fields as generic
from django.contrib.auth.signals import user_logged_in
from django.utils.timezone import now
from django_pgjson.fields import JsonBField

from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.signals import social_account_added
from allauth.account.adapter import get_adapter
from model_utils.managers import QueryManager
from rest_framework.renderers import JSONRenderer
from djorm_pgarray.fields import ArrayField
from monthdelta import monthdelta
from model_utils import FieldTracker
from linkedin import linkedin
from linkedin.exceptions import LinkedInError
from notifications.signals import notify
from phonenumber_field.modelfields import PhoneNumberField

from med_social.utils import (get_current_tenant, this_month, this_week,
                              humanized_datetime, today, humanized_date)
from med_social.auth_avatar import copy_avatar
from med_social.constants import OnboardingConstantsMixin as ONB
from med_social.constants import UserKindConstantsMixin as KIND
from med_social.libs.mixins import BaseUser
from med_social.utils import track_event

from projects.models import Project, ProposedResourceStatus
from reviews.models import Review
from reviews.db.fields import ReviewsField
from vendors.models import ProcurementContact
from .tasks import first_time_login_task, signup_task

logger = logging.getLogger(__name__)


class ActiveUserManager(UserManager):
    def get_queryset(self):
        return super(ActiveUserManager, self).get_queryset().filter(
            is_deleted=False)

    def all_with_deleted(self):
        return super(ActiveUserManager, self).get_queryset().all()


def _get_resume_upload_path(instance, filename):
    tenant = connection.tenant
    t = "{tenant_id}".format(tenant_id=tenant.id)
    u = "{user_id}".format(user_id=instance.id)
    fn, ext = os.path.splitext(filename)
    fname = "{username}-resume.{ext}".format(username=instance.username,
                                             ext=ext)
    return os.path.join(settings.PROTECTED_ROOT, t, 'r', u, fname)


class ReviewableMixin(models.Model):
    reviews = ReviewsField(Review)

    class Meta:
        abstract = True

    def get_all_reviews(self):
        proposed = self.proposed.values_list('id', flat=True)
        proposed_ct = ContentType.objects.get_for_model(self.proposed.model)
        user_ct = ContentType.objects.get_for_model(self)

        q = Q(content_type=proposed_ct, object_id__in=proposed)
        q = q | Q(content_type=user_ct, object_id=self.id)
        return Review.objects.filter(q)

    def __Reviews__denorm_reviews__(self, commit=True):
        reviews = self.get_all_reviews()
        self.avg_score = reviews.aggregate(
            Avg('score'))['score__avg']
        self.reviews_count = reviews.count()

        if commit:
            self.save(update_fields=('avg_score', 'reviews_count'))


def _default_user_meta():
    return {}


class User(BaseUser, ReviewableMixin, ONB, KIND):
    search_template = 'users/search_result.html'

    NONE = 0
    KIND_CLIENT = 1
    KIND_VENDOR = 2
    KIND_CHOICES = (
        (KIND_CLIENT, 'Client',),
        (KIND_VENDOR, 'Vendor',),
    )
    ROLE_SOFTWARE_DEV = 1
    ROLE_BUSINESS_ANALYSIS = 2
    ROLE_ACCOUNT_MANAGEMENT = 3
    ROLE_VENDOR_MANAGEMENT = 4
    ROLE_PROJECT_MANAGEMENT = 4

    ROLE_CHOICES = (
        (ROLE_SOFTWARE_DEV, 'Software Development'),
        (ROLE_BUSINESS_ANALYSIS, 'Business Analysis'),
        (ROLE_ACCOUNT_MANAGEMENT, 'Account Management'),
        (ROLE_VENDOR_MANAGEMENT, 'Vendor Management'),
        (ROLE_PROJECT_MANAGEMENT, 'Project Management'),
    )

    PERMISSIONS = (
        ('invite_user', 'Can invite user', Permission.ALL, False),
        ('delete_user', 'Can delete user', None, True),
        ('manage_features', 'Can manage features', Permission.CLIENT, True),
    )
    # manage_features: should be on customers but customers table is only
    # synched to public schema so we have put it here instead

    _cached_following = []

    communities = models.ManyToManyField('customers.Customer', related_name='users', blank=True)
    username = models.CharField(
        _('username'), max_length=30, unique=True,
        help_text=_('30 characters or fewer. Letters, numbers, _ and . (dot) characters'),
        validators=[
            validators.RegexValidator(re.compile('^%s$' % '^\w+[\w+.-]*'), _('Enter a valid username.'), 'invalid')
        ], default=None)
    email = models.EmailField(_('email address'), max_length=254, unique=True, blank=False, null=False)

    bio = models.TextField(default='', max_length=140)

    meta = JsonBField(default=_default_user_meta, blank=True)
    invited_by = models.ManyToManyField(
        'self', related_name='invited_users', through='UserInvitation', symmetrical=False)

    # Relationships
    vendor = models.ForeignKey('vendors.Vendor', blank=True, null=True, related_name='users')
    categories = models.ManyToManyField('categories.Category', related_name='users')
    divisions = models.ManyToManyField(
        'divisions.Division', through='UserDivisionRel', related_name='users', blank=True)

    # State fields
    next_available = models.DateField(blank=True, null=True, editable=False, default=None)
    is_deleted = models.BooleanField(_('delete'), default=False)
    is_staffable = models.BooleanField(
        'Staffable', default=True, help_text=_('Can this person be staffed on projects?'))

    kind = models.PositiveSmallIntegerField(choices=KIND_CHOICES, default=KIND_VENDOR)
    pending_setup_steps = ArrayField(verbose_name=_('Pending steps'), default='{1, 3}', dbtype="int", dimension=1)
    # pending_setup_steps = ArrayField(
    #     verbose_name=_('Pending steps'), default=ONB.SETUP_STEPS_DEFAULT, dbtype="int", dimension=1)
    first_login = models.DateTimeField(null=True, blank=True)

    # Profile fields
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    headline = models.TextField(_('headline'), max_length=140, blank=True, default='')
    summary = models.TextField(_('summary'), max_length=1023, blank=True, default='')
    roles = models.ManyToManyField('roles.Role', related_name='users')

    resume = models.FileField(null=True, upload_to=_get_resume_upload_path)
    linkedin_profile_url = models.URLField(null=True)
    location = models.ForeignKey('locations.Location', null=True)
    skill_level = models.ForeignKey('categories.SkillLevel', null=True)
    phone = PhoneNumberField(null=True, blank=True)
    organization_name = models.CharField(_('organization'), max_length=124, blank=True)
    tracker = FieldTracker(fields=['password'])

    # generic relation reverse API enablers
    notes = generic.GenericRelation('notes.Note')
    metric = generic.GenericRelation('metrics.Metric')

    objects = UserManager()
    staffable = QueryManager(is_staffable=True)

    # Notification Settings
    text_rfp_new = models.BooleanField('TEXT: When a new RFP that fits my services is posted', default=True)
    text_rfp_message = models.BooleanField('TEXT: When I get a question on my proposal', default=True)
    text_bid_change = models.BooleanField('TEXT: When a vendor posts a bid', default=True)
    text_bid_win = models.BooleanField('TEXT: When my bid wins the contract', default=True)
    text_bid_lose = models.BooleanField('TEXT: When my bid loses the contract', default=True)
    email_rfp_new = models.BooleanField('EMAIL: When a new RFP that fits my services is posted', default=True)
    email_rfp_message = models.BooleanField('EMAIL: When I get a question on my proposal', default=True)
    email_bid_change = models.BooleanField('EMAIL: When a vendor posts a bid', default=True)
    email_bid_win = models.BooleanField('EMAIL: When my bid wins the contract', default=True)
    email_bid_lose = models.BooleanField('EMAIL: When my bid loses the contract', default=True)

    def save(self, *args, **kwargs):
        if self._orig_kind != self.kind:
            self.pending_setup_steps = self.SETUP_STEPS
        pending_set = set(self.pending_setup_steps)
        allowed_set = set(self.SETUP_STEPS)
        self.pending_setup_steps = list(allowed_set.intersection(pending_set))
        self.pending_setup_steps.sort()
        self.headline = self.headline.strip()
        self.summary = self.summary.strip()
        self.username = self.username.lower()

        if self.has_joined:
            if (self.tracker.has_changed('password') and self.tracker.changed().get('password') and
                    self.SETUP_PASSWORD_SET in self.pending_setup_steps):
                self.pending_setup_steps.remove(self.SETUP_PASSWORD_SET)

        return super(User, self).save(*args, **kwargs)

    def __unicode__(self):
        return self.get_name_display()

    @staticmethod
    def autocomplete_search_fields():
        return ('id__iexact', 'username__icontains', 'email__icontains')

    def get_name_display(self):
        return self.get_full_name() or self.get_short_name() or self.email

    def get_company_display(self):
        if self.vendor_id:
            return self.vendor.name
        else:
            if connection.tenant.is_public_instance:
                return self.organization_name
            return get_current_tenant().name

    def get_suggested_clients(self):
        suggested = self.meta.get('suggested_clients', [])
        from vendor_profiles.models import Client
        return Client.objects.filter(is_partner=True, id__in=suggested)

    def get_user_hash(self):
        INTERCOM_SECRET = 'xtsAmAxmU7kW0B9XTE1qrjmg5vJFxTJ3Fu4_9AOH'
        return hmac.new(INTERCOM_SECRET, str(self.pk), digestmod=hashlib.sha256).hexdigest()

    def get_sender_line(self):
        return '{} <{}>'.format(self, self.email)

    @classmethod
    def get_suggested_resources(cls, **kwargs):
        fields = {
            'location': 'location',
            'skill_level': 'skill_level',
            'categories': 'categories__in',
            'role': 'roles'
        }

        query_kwargs = {}
        for key, value in kwargs.items():
            if value and key in fields:
                query_kwargs[fields[key]] = value
        if query_kwargs:
            users = cls.objects.filter(**query_kwargs)
        else:
            users = cls.objects.none()

        start = kwargs.get('start_date')
        if start:
            users = users.exclude(proposed__start_date__lte=start, proposed__end_date__gte=start)

        end = kwargs.get('end_date')
        if end:
            users = users.exclude(proposed__start_date__lte=end, proposed__end_date__gte=end)

        if start and end:
            users = users.exclude(proposed__start_date__gte=start, proposed__start_date__lte=end)
            users = users.exclude(proposed__end_date__gte=start, proposed__end_date__lte=end)

        return users.distinct()

    @classmethod
    def get_management_user(cls):
        return cls.objects.get(username='management')

    @property
    def SETUP_STEPS(self):
        """
        Currently the system has 3 on-boarding steps:
        SETUP_LINKEDIN_FETCH = 1
        - fetch data from the linkedin
        - this step gets completed in the post_save signal after
        the social accounts get created. (check signals below)
        """
        if connection.schema_name == 'public':
            return []
        if self.is_vendor:
            if self.is_first_user:
                return self.SETUP_STEPS_FIRST_VENDOR
            return self.SETUP_STEPS_VENDOR
        elif self.is_client:
            if self.is_first_user:
                return self.SETUP_STEPS_FIRST_CLIENT
            return self.SETUP_STEPS_CLIENT
        else:
            return self.SETUP_STEPS_DEFAULT

    @property
    def last_updated_availability(self):
        return self.meta.get('last_updated_availability', None)

    @last_updated_availability.setter
    def last_updated_availability(self, value):
        self.meta['last_updated_availability'] = value

    @property
    def natural_last_udpated_availability(self):
        return humanized_datetime(self.last_updated_availability)

    @property
    def is_first_user(self):
        return self.meta.get('is_first_user', False)

    @property
    def is_client(self):
        return self.kind == self.KIND_CLIENT

    @property
    def is_allowed_change(self):
        return self.is_client and self.is_superuser

    @property
    def is_vendor(self):
        return self.kind == self.KIND_VENDOR

    @property
    def has_joined(self):
        return bool(self.first_login)

    @property
    def next_setup_step(self):
        try:
            return self.pending_setup_steps[0]
        except (IndexError, TypeError):
            return None

    @property
    def next_step_display(self):
        return self.SETUP_STEPS_DICT.get(self.next_setup_step, '').replace('_', ' ').capitalize()

    @property
    def has_completed_onboarding(self):
        return False if len(self.pending_setup_steps) else True

    @property
    def setup_step_url(self):
        next_step = self.next_setup_step
        if next_step:
            args = ()
            if self.is_vendor and self.vendor and next_step == self.SETUP_VENDOR_PROFILE:
                args = (self.vendor.id,)
            return reverse('user_setup:setup_step_%s' % self.SETUP_STEPS_DICT[next_step], args=args)
        else:
            return None

    @property
    def linkedin_account(self):
        return self.socialaccount_set.filter(provider='linkedin').first()

    @property
    def cached_following(self):
        if not self._cached_following:
            self._cached_following = self.following.values_list('id',
                                                                flat=True)
        return self._cached_following

    def as_json(self):
        from API.serializers.user_serializers import UserSerializer
        return JSONRenderer().render(UserSerializer(self).data)

    def get_avatar_url(self):
        try:
            return self.avatar_set.get(primary=True).avatar_url(45)
        except:
            return None

    def get_initials(self):
        return '{}{}'.format(self.first_name[0] if self.first_name else '',
                             self.last_name[0] if self.last_name else '')

    @property
    def next_available_in_future(self):
        available = self.get_next_available_date
        return available > today()

    @property
    def get_next_available_date(self):
        return self.next_available

    @property
    def get_next_available_date_display(self):
        if self.get_next_available_date:
            return humanized_date(self.get_next_available_date)
        else:
            return 'Unknown'

    @property
    def get_next_available_css_class(self):
        _today = today()
        date = self.get_next_available_date
        if date <= _today:
            return 'text-danger'
        elif date <= _today + timedelta(days=14):
            return 'text-warning'
        return ''

    @property
    def is_procurement(self):
        if self.is_client:
            return ProcurementContact.objects.filter(user=self).exists()
        return False

    def calculate_next_available_date(self):
        # FIXME: optimize by comparing ranges, not dates.

        # Fetch future allocations sorted by start_date
        _today = today()
        _range = self.proposed.filter(
            start_date__lte=_today, end_date__gte=_today, allocation__gt=0,
        ).order_by('start_date').values_list('start_date', 'end_date')

        if not _range:
            last_allocation = self.proposed.filter(end_date__lte=_today, allocation__gt=0).order_by('-end_date').first()
            if last_allocation:
                return last_allocation.end_date
            else:
                return None

        # create sorted list of all unavailabel dates
        dates = []
        for R in _range:
            date = R[0]
            while date <= R[1]:
                dates.append(date)
                date = date + timedelta(days=1)
        dates = sorted(set(dates))

        # find the first missing date in busy dates
        natural_date = dates[0]
        for date in dates:
            if date != natural_date:
                break
            natural_date += timedelta(days=1)
        return natural_date

    def get_availability(self):
        months = {}
        _this_month = this_month()
        fetch_upto = _this_month + monthdelta(4)
        weeks = self.availability_weeks.filter(date__gte=_this_month,
                                               date__lte=fetch_upto)
        for week in weeks:
            months[week.month] = months.get(week.month, [])
            months[week.month].append(week)
        return sorted(tuple(months.items()))

    def get_availability_as_weeks(self):
        _this_week = this_week()
        fetch_upto = this_month() + monthdelta(2)

        db_weeks = iter(self.availability_weeks.filter(date__gte=_this_week,
                                                       date__lte=fetch_upto))
        weeks = []
        # last_day_of_last_week = fetch_upto + datetime.timedelta(days=6)
        last_day_of_last_week = fetch_upto
        day = _this_week
        fetch_next = True
        FakeWeek = namedtuple('Week', ['date', 'allocation', 'is_fake', 'user'])
        while day <= last_day_of_last_week:
            first_day_of_week = day - datetime.timedelta(days=day.weekday())
            if fetch_next:
                try:
                    real_week = db_weeks.next()
                except StopIteration:
                    real_week = None

            if real_week and real_week.date == first_day_of_week:
                fetch_next = True
                week = real_week
            else:
                fetch_next = False
                week = None

            if not week:
                week = FakeWeek(first_day_of_week, None, True, self)

            weeks.append(week)
            day = day + datetime.timedelta(days=7)
        return weeks

    def get_rate(self, role, location=None, skill_level=None):
        location = location or self.location
        skill_level = skill_level or self.skill_level
        applied_rate = None

        from rates.models import Rate

        try:
            applied_rate = self.rate
        except Rate.DoesNotExist:
            applied_rate = None

        if self.is_vendor:
            try:
                rates = Rate.global_cards.filter(
                    location=location,
                    skill_level=skill_level,
                    role=role,
                    vendor=self.vendor
                )
                if rates.count():
                    applied_rate = rates.first()
            except:
                applied_rate = None
        else:
            rates = Rate.global_cards.filter(
                location=location,
                skill_level=skill_level,
                role=role,
                vendor__isnull=True
            )
            if rates.count():
                applied_rate = rates.first()
        return applied_rate

    def get_absolute_url(self):
        return reverse('users:profile', args=(self.username,))

    def get_profile_modal_url(self):
        return reverse('users:profile_modal', args=(self.username,))

    def reset_setup_steps(self):
        self.pending_setup_steps = self.SETUP_STEPS

    def complete_setup_step(self, step):
        try:
            self.pending_setup_steps.remove(step)
        except ValueError:
            pass

    def add_setup_step(self, step):
        if step not in self.pending_setup_steps:
            self.pending_setup_steps.append(step)

    def get_linkedin_url(self):
        if self.linkedin_profile_url:
            return self.linkedin_profile_url
        else:
            try:
                return self.linkedin_account.get_profile_url()
            except AttributeError:
                return ''

    def send_welcome_email(self, tenant):
        get_adapter().send_mail('customers/email/welcome', self.email,
                                {'user': self, 'current_tenant': tenant})

    def send_approval_email(self):
        current_site = Site.objects.get_current()
        ctx = {
            "user": self,
            "current_site": current_site,
        }
        email_template = 'account/email/accepted'
        get_adapter().send_mail(email_template, self.email, ctx)

    def send_customer_admin_welcome_email(self, tenant, pwd, direct_url):
        url = ''.join([settings.DEFAULT_HTTP_PROTOCOL, tenant.domain_url])
        ctx = {
            "username": self.username,
            "password": pwd,
            "company": tenant.name,
            "url": url,
            "direct_url": ''.join([url, direct_url]),
            "reset_password_url": ''.join(
                [url, reverse('account_change_password')]),
        }
        email_template = 'account/email/client_admin_welcome'
        get_adapter().send_mail(email_template, self.email, ctx)

    def send_rejection_email(self):
        return
        """
        current_site = Site.objects.get_current()
        ctx = {
            "user": self,
            "current_site": current_site,
        }
        email_template = 'account/email/rejected'
        get_adapter().send_mail(email_template, self.email, ctx)
        """

    def send_first_login_notification(self, recipients):
        data = dict(sender=self, description='', verb='has logged in for the first time')
        for recipient in recipients:
            data['recipient'] = recipient
            notify.send(**data)

    def _parse_date(self, d):
        return date(year=d.get('year'), month=d.get('month', 1), day=d.get('day', 1)) if d else None

    def _update_defaults(self, obj, defaults):
        for field, value in defaults.iteritems():
            setattr(obj, field, value)
        obj.save()

    def __populate_linkedin_profile(self, profile=None, commit=True):
        try:
            profile = self.get_linkedin_profile(profile)
        except LinkedInError:
            return False
        if not profile:
            return
        self.headline = profile.get('headline', self.headline)
        self.summary = profile.get('summary', self.summary)
        if commit:
            self.save(update_fields=('headline', 'summary',))

    def populate_linkedin_profile(self, profile=None, commit=True):
        try:
            profile = self.get_linkedin_profile(profile)
        except LinkedInError:
            return False
        if not profile:
            return

        self.first_name = profile.get('firstName', self.first_name)
        self.last_name = profile.get('lastName', self.last_name)
        self.headline = profile.get('headline', self.headline)
        self.summary = profile.get('summary', self.summary)
        if commit:
            self.save(update_fields=('first_name', 'last_name',))
            self.save(update_fields=('headline', 'summary',))

        # @TODO: Fetch large size avatar from linkedin

    def get_linkedin_profile(self, profile=None, selectors=None):
        if not selectors:
            # selectors = ['headline', 'summary',]
            # selectors = ['headline', 'summary', 'first-name', 'last-name']
            selectors = []
        if not profile:
            account = self.linkedin_account
            if not account:
                return
            token = account.socialtoken_set.all().first()
            if not token:
                return
            app = token.app
            auth = linkedin.LinkedInDeveloperAuthentication(
                app.client_id, app.secret, token.token, token.token_secret, reverse('linkedin_callback'),
                ('r_emailaddess', 'r_fullprofile', 'r_basicprofile'),
            )
            application = linkedin.LinkedInApplication(auth)
            profile = application.get_profile(selectors=selectors)
        return profile

    def get_recent_project(self):
        return Project.objects.filter(
            proposals__resource=self, proposals__status__value=ProposedResourceStatus.SUCCESS,
        ).order_by('-end_date').first()


class UserDivisionRel(models.Model):
    user = models.ForeignKey('users.User', related_name='division_rels')
    division = models.ForeignKey('divisions.Division', related_name='user_rels')
    is_admin = models.BooleanField(default=False)

    class Meta:
        unique_together = (('user', 'division',),)

    def __unicode__(self):
        r = '{} @ {} '.format(self.user.get_name_display(), self.division)
        if self.is_admin:
            r = '[ADMIN] {}'.format(r)
        return r


class UserInvitation(models.Model):
    uuid = models.UUIDField(blank=True, db_index=True, default=uuid.uuid4, editable=False)
    receiver = models.ForeignKey(User, related_name='invitations')
    sender = models.ForeignKey(User, related_name='invitations_sent', null=True, blank=True)

    expires_at = models.DateTimeField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (('sender', 'receiver',),)

    def get_absolute_url(self):
        return reverse("users:direct_join", args=(self.uuid,))


@receiver(post_init, sender=User, dispatch_uid='users.User.pre_save')
def post_user_init(sender, **kwargs):
    user = kwargs['instance']
    created = kwargs.get('created')

    if user.id is None and user.kind:
        user.pending_setup_steps = user.SETUP_STEPS
    user._orig_kind = user.kind

    if created:
        if user.meta.get('is_first_user') and user.is_vendor:
            vendor = user.vendor
            vendor.contacts.add(user)


@receiver(social_account_added, dispatch_uid='users.social_account.post_creation')
def post_social_account_creation(sender, **kwargs):
    request = kwargs['request']
    user = request.user
    user.populate_linkedin_profile()
    account = user.socialaccount_set.first()
    if account:
        copy_avatar(request, user, account)


@receiver(post_save, sender=SocialAccount, dispatch_uid='users.social_account.post_save')
def post_social_account_save(sender, **kwargs):
    if kwargs['raw']:
        return
    instance = kwargs['instance']
    user = instance.user
    if user:
        user.complete_setup_step(user.SETUP_LINKEDIN_FETCH)
        user.save()


@receiver(user_logged_in, dispatch_uid='users.login.post_user_logged_in')
def post_login_notification(**kwargs):
    user = kwargs.get('user')

    new_user = user and not user.has_joined

    partner_id = kwargs['request'].session.get('partner_id', None)
    if partner_id:
        suggested = user.meta.get('suggested_clients', [])
        suggested.append(partner_id)
        user.meta['suggested_clients'] = list(set(suggested))
        if not new_user:
            user.save()

    if new_user:
        track_event(
            'user:first_login',
            {
                'user_id': user.id,
                'user': user.username,
                'is_client': user.is_client,
            },
        )
        user.first_login = now()
        user.save()
        first_time_login_task.delay(user_id=user.id,
                                    tenant_id=connection.tenant.id)


class SignupToken(models.Model):
    uuid = models.UUIDField(blank=True, db_index=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(_('first name'), max_length=254, blank=True)
    last_name = models.CharField(_('last name'), max_length=254, blank=True)
    email = models.EmailField(_('email address'), max_length=254)
    expires_at = models.DateTimeField()
    created = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    is_invited = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)

    def get_absolute_url(self):
        return reverse("users:register", args=(self.uuid,))

    def get_confirm_url(self):
        return reverse("users:confirm_register", args=(self.uuid,))


@receiver(post_save, sender=SignupToken, dispatch_uid='users.signup_token.post_save')
def post_signup_token_save(sender, **kwargs):
    instance = kwargs['instance']
    created = kwargs['created']

    if created:
        signup_task.delay(token_id=instance.id, tenant_id=connection.tenant.id)


def get_notification_receivers(self):
        return []


class SEOMetadata(models.Model):
    path = models.CharField(max_length=255)
    title = models.CharField(max_length=68)
    description = models.TextField(blank=True)
    keywords = models.TextField(blank=True)

    def __unicode__(self):
        return self.path
