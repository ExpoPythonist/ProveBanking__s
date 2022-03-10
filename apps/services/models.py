from django.db import models

from med_social.utils import humanized_datetime
from vendors.models import Vendor


class Service(models.Model):
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, null=True)
    vendors = models.ManyToManyField(Vendor,
                                     through='ServiceVendor',
                                     related_name='services')

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('created',)

    def __unicode__(self):
        return self.name

    @property
    def natural_created_date(self):
        return humanized_datetime(self.created)

    def get_vendor_contact(self, vendor):
        sv = ServiceVendor.objects.filter(service=self, vendor=vendor).first()
        return sv


class ServiceVendor(models.Model):
    service = models.ForeignKey(Service)
    vendor = models.ForeignKey(Vendor)
    contact_user = models.ForeignKey('users.User',
                                     null=True,
                                     related_name='vendor_contacts')

    def __unicode__(self):
        return "%s by %s" % (self.service.name, self.vendor.name)
