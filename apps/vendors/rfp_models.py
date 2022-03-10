from __future__ import unicode_literals
import os
import datetime
import imghdr
import urlparse
import uuid

from datetime import date
from decimal import Decimal
from math import log

from dateutil.parser import parse

from django.db import models
from django.db.models import Count, Q, Avg, Sum
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes import fields as generic
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericRelation
from django.utils.crypto import get_random_string
from django.utils.encoding import python_2_unicode_compatible
from django.utils.timezone import now
from django_pgjson.fields import JsonBField

from rest_framework.renderers import JSONRenderer
from autoslug.fields import AutoSlugField
from simple_activity.decorators import register_model
from djorm_pgarray.fields import ArrayField, TextArrayField
from notifications.signals import notify
from phonenumber_field.modelfields import PhoneNumberField
from picklefield.fields import PickledObjectField
from post_office import mail
from sorl.thumbnail import ImageField
from model_utils import FieldTracker
from django_pgjson.fields import JsonBField
from uuidfield import UUIDField

from med_social.utils import slugify
from med_social.utils import humanized_datetime
from med_social.utils import get_score_level
from med_social.utils import get_current_tenant

from categories.models import Category
from notes.models import Note
from reviews.db.fields import ReviewsField
from reviews.models import Review
from metrics.models import Metric, MetricAggregate


@python_2_unicode_compatible
class RFP(models.Model):
    MASKED_EXPIRY = (
        ('1 hour', '1 hour'),
        ('5 hours', '5 hours'),
        ('24 hours', '24 hours'),
        ('2 days', '2 days'),
        ('1 week', '1 week'),
    )
    client = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='rfps')
    vendors = models.ManyToManyField('vendors.Vendor', related_name='rfps', through='Bid', blank=True, verbose_name='Companies you\'ve chosen')
    categories = models.ManyToManyField(Category, related_name='rfps', blank=True)
    open_rfp = models.BooleanField(default=False)

    question = models.CharField('What do you want done?', max_length=1000)
    description = models.TextField('Please describe the job in more detail', blank=True)

    masked = models.BooleanField('Keep my number hidden', default=False)
    masked_phone = PhoneNumberField(blank=True)
    masked_expiry = models.CharField(choices=MASKED_EXPIRY, max_length=10, blank=True)

    notif_call = models.BooleanField('Allow call?', default=False)
    notif_text = models.BooleanField('Notify through text?', default=True)
    notif_email = models.BooleanField('Notify through email?', default=True)

    uuid = UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    date_deleted = models.DateTimeField(blank=True, null=True, editable=False)

    class Meta:
        ordering = ('date_created',)
        verbose_name = 'RFP'

    def __str__(self):
        return '{}: {}'.format(self.client, self.question)

    def get_absolute_url(self):
        return reverse('rfp_view', args=(self.client.username, self.uuid))

    @property
    def messages(self):
        return Message.objects.filter(bid__rfp=self)

    def has_winner(self):
        return self.bids.filter(winner=True).exists()


@python_2_unicode_compatible
class Bid(models.Model):
    rfp = models.ForeignKey(RFP, related_name='bids')
    vendor = models.ForeignKey('vendors.Vendor', related_name='bids')

    bid = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    description = models.TextField(blank=True)
    winner = models.BooleanField(default=False)

    masked_phone = PhoneNumberField(blank=True)

    uuid = UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    date_deleted = models.DateTimeField(blank=True, null=True, editable=False)

    class Meta:
        ordering = ('date_created',)

    def __str__(self):
        return '{} < {}'.format(self.vendor, self.rfp)

    @classmethod
    def filter_by_user(cls, user):
        return cls.objects.filter(models.Q(vendor__users=user) | models.Q(rfp__client=user)).distinct()

    def get_rank(self):
        if self.bid is not None:
            bids = sorted(self.rfp.bids.filter(bid__isnull=False).values_list('bid', flat=True))
            return bids.index(self.bid) + 1
        return self.rfp.bids.count()

    def get_absolute_url(self):
        return reverse('bid_view', args=(self.vendor.users.first().username, self.uuid))

    def save(self, *args, **kwargs):
        if not self.pk:
            self.notify('rfp_new')
        else:
            old = Bid.objects.get(pk=self.pk)
            if old.bid != self.bid:
                self.notify('bid_change')
                self.messages.create(message='{} updated the bid to ${}'.format(self.vendor, self.bid))
            if old.winner != self.winner and self.winner:
                self.notify('bid_win')
        super(Bid, self).save(*args, **kwargs)

    def notify(self, message_type):
        if message_type == 'rfp_new':
            for user in self.vendor.users.all():
                notify.send(self.rfp.client, verb='created the RFP', action_object=self, target=self, recipient=user)
                notify_user(user, 'New Request for Proposal: {} {}'.format(
                    self.rfp,
                    'http://dev-provencompany.marcelo.ph' + reverse('bid_view', args=[user.username, self.uuid])
                ))
        if message_type == 'bid_change':
            user = self.rfp.client
            notify.send(self.vendor, verb='posted a bid on', action_object=self, target=self.rfp, recipient=user)
            notify_user(user, 'New Bid Update from {}: {} {}'.format(
                self.vendor, self.bid,
                'http://dev-provencompany.marcelo.ph' + reverse('bid_view', args=[user.username, self.uuid])
            ))
        if message_type == 'bid_win':
            for user in self.vendor.users.all():
                notify.send(self.vendor, verb='won the RFP', action_object=self, target=self, recipient=user)
                notify_user(user, 'Congratulations! Your bid won the RFP: {}'.format(
                    self.rfp,
                    'http://dev-provencompany.marcelo.ph' + reverse('bid_view', args=[user.username, self.uuid])
                ))
            for other in Bid.objects.exclude(pk=self.pk).filter(rfp=self.rfp, bid__gt=0):
                for user in other.vendor.users.all():
                    notify.send(self.vendor, verb='lost the RFP', action_object=self, target=self, recipient=user)
                    notify_user(user, 'Sorry! Your bid lost the RFP: {}'.format(
                        self.rfp,
                        'http://dev-provencompany.marcelo.ph' + reverse('bid_view', args=[user.username, self.uuid])
                    ))


@python_2_unicode_compatible
class Message(models.Model):
    bid = models.ForeignKey(Bid, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='rfp_messages', blank=True, null=True)
    message = models.TextField(blank=True)

    uuid = UUIDField(default=uuid.uuid4, editable=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)
    date_deleted = models.DateTimeField(blank=True, null=True, editable=False)

    class Meta:
        ordering = ('date_created',)

    def __str__(self):
        return '{} | {} {}: {}'.format(self.bid, self.date_created, self.sender, self.message)

    def get_absolute_url(self):
        return reverse('bid_view', args=(self.sender.username, self.bid.uuid))

    def save(self, *args, **kwargs):
        if not self.pk and self.sender:
            self.notify()
        super(Message, self).save(*args, **kwargs)

    def notify(self):
        if self.sender == self.bid.rfp.client:
            for user in self.bid.vendor.users.all():
                notify.send(self.sender, verb='replied to', action_object=self.bid, target=self.bid.rfp, recipient=user)
                notify_user(user, 'New message from {} on "{}": {} {}'.format(
                    self.sender.first_name, self.bid.rfp.question, self.message,
                    'http://dev-provencompany.marcelo.ph' + reverse('bid_view', args=[user.username, self.bid.uuid])
                ))
        else:
            user = self.bid.rfp.client
            notify.send(self.sender, verb='replied to', action_object=self.bid, target=self.bid.rfp, recipient=user)
            notify_user(user, 'New message from {} of {} on "{}": {} {}'.format(
                self.sender.first_name, self.bid.vendor, self.bid.rfp.question, self.message,
                'http://dev-provencompany.marcelo.ph' + reverse('bid_view', args=[user.username, self.bid.uuid])
            ))


from lightrfp.notifs import notify_user
