import re

from django.db import models
from django.db.models import Q
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver

from filtered_contenttypes.fields import FilteredGenericForeignKey

from med_social.utils import humanized_datetime
from vendors.models import Vendor
from activity.models import Event


class Channel(models.Model):
    name = models.CharField(max_length=127, default='', blank=True)
    content_type = models.ForeignKey(ContentType, related_name='channels')
    object_id = models.PositiveIntegerField()
    content_object = FilteredGenericForeignKey('content_type', 'object_id')
    users = models.ManyToManyField('users.User', verbose_name='members', related_name='channels')
    created_by = models.ForeignKey('users.User', null=True, related_name='created_channels')
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return 'discussion'

    def get_absolute_url(self):
        return '{}?active_tab=channel-{}'.format(
            self.content_object.get_absolute_url(),
            self.id
        )

    def get_event_url(self):
        content_type = ContentType.objects.get_for_model(Channel)
        return reverse('activity:event_update', args=(content_type.id,
                                                      self.id))

    def get_invite_user_url(self):
        return reverse('channels:invite_user', args=(self.id,))

    def post_event_object_delete(self, user):
        pass

    # def create_event_object(self, user):
    #     content_type = ContentType.objects.get_for_model(Channel)
    #     Event.objects.get_or_create(user=user,
    #                                 content_type_id=content_type.id,
    #                                 object_id=self.id,)
    #     self.content_object.create_event_object(user=user)

    @property
    def natural_created_date(self):
        return humanized_datetime(self.created)

    @property
    def latest_comment(self):
        return self.comments.latest()

    @property
    def html_id(self):
        return 'channel-{}'.format(self.id)


class Message(models.Model):
    channel = models.ForeignKey(Channel, related_name='messages')
    body = models.TextField('Message')
    mentions = models.ManyToManyField('users.User', related_name='mentions')
    viewed = models.ManyToManyField('users.User', related_name='read_messages')
    posted_by = models.ForeignKey('users.User', null=True, related_name='messages')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('created',)
        get_latest_by = 'created'

    def save(self, *args, **kwargs):
        pattern = '(?<=^|(?<=[^a-zA-Z0-9-_\.]))@([A-Za-z0-9_\.]+)'
        usernames = re.findall(pattern, self.body)

        emails = re.findall(settings.EMAIL_REGEX, self.body)

        pq = Q(username__in=usernames) | Q(email__in=emails)
        users = get_user_model().objects.filter(pq)

        #self.body_html = self.get_as_html(users)
        ret_val = super(Message, self).save(*args, **kwargs)
        self.mentions.clear()
        self.mentions.add(*users)
        return ret_val

    def get_absolute_url(self):
        return self.channel.get_absolute_url()

    @property
    def body_html(self):
        html = self.body
        for user in self.mentions.all():
            html = re.sub(
                '(?<!\S)@{}(?!\S)'.format(user.username),
                '<a href="{}" data-toggle="modal"'
                ' data-target="#userModal">@{}</a>'.format(
                    user.get_profile_modal_url(),
                    user.username),
                html
            )
            # FIXME: replace this with regex
            if user.email in html:
                html = html.replace(
                    user.email,
                    ('{} (<a href="{}" data-toggle="modal" '
                     'data-target="#userModal">@{}</a>)').format(
                        user.email,
                        user.get_profile_modal_url(),
                        user.username
                    )
                )
        return html

    @property
    def natural_created_date(self):
        return humanized_datetime(self.created)


@receiver(post_save, sender=Message,
          dispatch_uid='channels.Message.post_save')
def post_message_saved(sender, **kwargs):
    if kwargs.get('created'):
        instance = kwargs.get('instance')
