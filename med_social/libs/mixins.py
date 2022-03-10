from django.core.mail import send_mail
from django.conf import settings
from django.db import models
from django.contrib.auth.models import (AbstractBaseUser, Permission, Group,
        UserManager, auth, _user_has_module_perms, _user_has_perm,
        _user_get_all_permissions)
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


class BaseUser(AbstractBaseUser):
    '''
    Extends AbstractBaseUser and implements required things for django
    permissions to work in admin. Most of this is borrowed from
    'auth.models.AbstractUser'.
    '''
    is_staff = models.BooleanField(_('staff status'), default=False,
        help_text=_('Designates whether the user can log into this admin '
                    'site.'))
    is_active = models.BooleanField(_('active'), default=True,
        help_text=_('Designates whether this user should be treated as '
                    'active. Unselect this instead of deleting accounts.'))
    is_superuser = models.BooleanField(_('superuser status'), default=False,
        help_text=_('Designates that this user has all permissions without '
                    'explicitly assigning them.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    groups = models.ManyToManyField(Group, verbose_name=_('groups'),
        blank=True, help_text=_('The groups this user belongs to. A user will '
                                'get all permissions granted to each of '
                                'his/her group.'))
    user_permissions = models.ManyToManyField(Permission,
        verbose_name=_('user permissions'), blank=True,
        help_text='Specific permissions for this user.')

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        abstract = True

    def get_full_name(self):
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        return self.first_name

    def get_group_permissions(self, obj=None):
        '''
        Returns a list of permission strings that this user has through his/her
        groups. This method queries all available auth backends. If an object
        is passed in, only permissions matching this object are returned.
        '''
        permissions = set()
        for backend in auth.get_backends():
            if hasattr(backend, 'get_group_permissions'):
                if obj is not None:
                    permissions.update(backend.get_group_permissions(self,
                                                                     obj))
                else:
                    permissions.update(backend.get_group_permissions(self))
        return permissions

    def get_all_permissions(self, obj=None):
        return _user_get_all_permissions(self, obj)

    def has_perm(self, perm, obj=None):
        '''
        Returns True if the user has the specified permission. This method
        queries all available auth backends, but returns immediately if any
        backend returns True. Thus, a user who has permission from a single
        auth backend is assumed to have permission in general. If an object is
        provided, permissions for this specific object are checked.
        '''

        # Active superusers have all permissions.
        if self.is_active and self.is_superuser:
            return True

        # Otherwise we need to check the backends.
        return _user_has_perm(self, perm, obj)

    def has_perms(self, perm_list, obj=None):
        '''
        Returns True if the user has each of the specified permissions. If
        object is passed, it checks if the user has all required perms for this
        object.
        '''
        for perm in perm_list:
            if not self.has_perm(perm, obj):
                return False
        return True

    def has_module_perms(self, app_label):
        '''
        Returns True if the user has any permissions in the given app label.
        Uses pretty much the same logic as has_perm, above.
        '''
        # Active superusers have all permissions.
        if self.is_active and self.is_superuser:
            return True

        return _user_has_module_perms(self, app_label)

    def email_user(self, subject, message, from_email=settings.DEFAULT_FROM_EMAIL):
        '''
        Sends an email to this User.
        '''
        send_mail(subject, message, from_email, [self.email])


class SerializableMixin(object):
    def serialize_fields(self, fields):
        dictionary = {}
        for field in fields:
            if hasattr(self, field):
                dictionary[field] = getattr(self, field)
        return dictionary
